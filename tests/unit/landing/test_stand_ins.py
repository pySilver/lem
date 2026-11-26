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
    ("before", "after"),
    (
        ("", f"\n{FAILED}\n"),
        (f"\n{PLAIN}\n", f"\n{FAILED}\n"),
        (f"\n{PLAIN}\n\n{FAILED}\n", f"\n\n{FAILED}\n"),
    ),
    ids=("new line", "replace", "remove the old line"),
)
def test_a_failed_stand_in_replaces_its_old_line_once(before: str, after: str) -> None:
    record = task("open")
    record = replace(record, task=replace(record.task, stand_ins=(FIRST, SECOND)))
    body = merge_notes.body_of(CHECKS + before, record, None)
    assert body == CHECKS + after
    assert merge_notes.body_of(body, record, None) == body


def test_a_new_failure_after_go_on_does_not_change_the_earlier_stand_in() -> None:
    earlier = replace(FIRST, again=MOMENT + timedelta(seconds=30))
    assert stand_ins.lines((earlier, SECOND), "merger") == ((PLAIN, PLAIN),)
    assert stand_ins.lines((FIRST, SECOND), "reviewer") == ()


def test_a_stand_in_that_read_after_the_owners_go_on_is_a_line_beside_the_one_that_failed() -> (
    None
):
    gone_on = MOMENT + timedelta(minutes=2)
    later = replace(FIRST, at=MOMENT + timedelta(minutes=3))
    history = (replace(FIRST, again=gone_on), replace(SECOND, again=gone_on), later)
    assert stand_ins.lines(history, "merger") == ((PLAIN, FAILED), (PLAIN, PLAIN))
    assert stand_ins.finals(history) == (FAILED, PLAIN)
    record = task("open")
    record = replace(record, task=replace(record.task, stand_ins=history))
    for before in ("", f"\n{PLAIN}\n"):
        body = merge_notes.body_of(CHECKS + before, record, None)
        assert body == f"{CHECKS}\n{FAILED}\n\n{PLAIN}\n"
        assert merge_notes.body_of(body, record, None) == body
    assert merge_notes.wanted(record, None) == (FAILED, PLAIN)


def test_the_same_stand_in_kept_twice_is_one_line() -> None:
    assert stand_ins.lines((FIRST, FIRST), "merger") == ((PLAIN, PLAIN),)
    assert stand_ins.finals((FIRST, FIRST)) == (PLAIN,)
