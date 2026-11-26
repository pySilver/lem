"""The text of a merger's stand-in as it changes after the pull request opens."""

from datetime import timedelta

import pytest
from msgspec.structs import replace

from lem.app.landing import merge_notes, stand_ins
from lem.records.work import StandIn
from unit.landing.worlds import MOMENT, task

FIRST = StandIn(
    seat="merger",
    failed="codex/gpt-6.2-sol:high",
    took="claude/opus:high",
    error="tokens",
    at=MOMENT,
)
SECOND = StandIn(
    seat="merger",
    failed="claude/opus:high",
    error="login",
    at=MOMENT + timedelta(minutes=1),
)
PLAIN = (
    "- the merge agent was `claude/opus:high` in place of `codex/gpt-6.2-sol:high`: "
    "Codex had no tokens"
)
FAILED = (
    "- the merge agent was to be `claude/opus:high` in place of `codex/gpt-6.2-sol:high`: "
    "Codex had no tokens; then Claude Code gave an error too: Claude Code had no login"
)
CHECKS = "## Checks\n\n- the checks passed\n"


@pytest.mark.parametrize(
    "before",
    ("", f"\n{PLAIN}\n", f"\n{PLAIN}\n\n{FAILED}\n"),
    ids=("new line", "replace", "remove the old line"),
)
def test_a_failed_stand_in_replaces_its_old_line_once(before: str) -> None:
    record = task("open")
    record = replace(record, task=replace(record.task, stand_ins=(FIRST, SECOND)))
    body = merge_notes.body_of(CHECKS + before, record, None)
    assert body is not None
    assert PLAIN not in body.splitlines()
    assert body.splitlines().count(FAILED) == 1
    assert merge_notes.body_of(body, record, None) == body


def test_a_new_failure_after_go_on_does_not_change_the_earlier_stand_in() -> None:
    earlier = replace(FIRST, again=MOMENT + timedelta(seconds=30))
    assert stand_ins.lines((earlier, SECOND), "merger") == {PLAIN: PLAIN}
    assert stand_ins.lines((FIRST, SECOND), "reviewer") == {}
