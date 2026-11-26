"""The tab Checks and review: the refund line's as today's board draws it, a green proposal, a
landing's run that ended stopped or red with no command, a task that ended with neither card,
and a pruned task."""

from typing import TYPE_CHECKING, Literal

import msgspec
from msgspec.structs import replace

from fixtures.board import panel
from fixtures.board.moments import ago
from fixtures.board.receipt import SLUG
from lem.board.inputs.parts import Row
from lem.board.views import owed, rounds
from lem.board.views.checks.tab import checks
from lem.records.journal.landing import CheckEnd
from lem.records.journal.task import Summary
from lem.records.landing.record import Landing
from unit.board.views.afternoon import world
from unit.landing.worlds import REVIEWED

if TYPE_CHECKING:
    from pathlib import Path

    from lem.board.views.world import Seen


def test_the_refund_line_s_checks_and_review_are_today_s(tmp_path: Path) -> None:
    found = world(tmp_path)
    assert checks(found, owed.seen(found, SLUG)) == panel.CHECKS


def test_the_round_does_not_show_an_outside_defect_as_a_nit() -> None:
    assert REVIEWED.counts.outside == 1
    assert rounds.line(REVIEWED).endswith("clean, 0 must-fix, 0 should, 0 nit")


def test_a_green_proposal_says_what_green_means(tmp_path: Path) -> None:
    found = world(tmp_path)
    tab = checks(found, owed.seen(found, "footer-terms-typo"))
    assert tab.commands_said == "2 commands green"
    assert tab.rounds_said == "1 round"
    assert tab.rounds[0].head == "round 1, one read: clean, 0 must-fix, 0 should, 1 nit"
    assert tab.proposal and tab.proposal.said == "Proposed: green"
    assert tab.proposal.green and tab.proposal.green.startswith(
        "the checks passed with the bar where it was"
    )
    assert tab.proposal.reasons is None
    assert tab.commands_empty is None
    assert tab.rounds_empty is None


def landing(seen: Seen, outcome: Literal["red", "stopped"], say: str) -> Seen:
    """The refund line back in its landing, its run of the checks ended with no command."""
    record = seen.record
    end = CheckEnd(at=ago(470), outcome=outcome, say=say)
    task = replace(record.task, status="landing")
    again = replace(
        record, task=task, landing=Landing(phase="preparing"), journal=(end,)
    )
    return replace(seen, record=again)


def test_a_run_that_ended_stopped_or_red_with_no_command_is_one_row(
    tmp_path: Path,
) -> None:
    found = world(tmp_path)
    seen = owed.seen(found, SLUG)
    stopped = checks(found, landing(seen, "stopped", f"{SLUG}: the owner stopped them"))
    assert stopped.ended_run == Row(
        id="gate-end",
        look="lem",
        icon="xmark",
        head="The checks were stopped",
        subs=("the owner stopped them",),
    )
    assert stopped.commands_empty is None
    assert stopped.rounds_empty == (
        "The review comes after the machine checks, before anything is proposed"
    )
    red = checks(found, landing(seen, "red", ""))
    assert red.ended_run == Row(
        id="gate-end",
        look="bad",
        icon="triangle-exclamation",
        head="The checks are red",
    )


def test_a_task_that_ended_with_neither_card_says_so(tmp_path: Path) -> None:
    found = world(tmp_path)
    tab = checks(found, owed.seen(found, "why-export-is-slow"))
    assert tab == msgspec.convert(
        {"ended": "The task ended with no checks and no review on record"},
        type(tab),
    )


def test_a_pruned_task_says_what_went_with_its_journal(tmp_path: Path) -> None:
    found = world(tmp_path)
    seen = owed.seen(found, "footer-terms-typo")
    summary = Summary(
        at=ago(1),
        statuses=("building", "landed"),
        first=ago(52),
        last=ago(32),
        entries=12,
    )
    pruned = replace(seen, record=replace(seen.record, journal=(summary,)))
    tab = checks(found, pruned)
    assert tab.went and tab.went.id == "went-checks"
    assert tab.went.said.startswith(
        "Its runs of the checks, its review rounds and the proposal’s reasons went with "
        "its events"
    )
    assert tab.went.artifacts.href == "/studio/shop/tasks/footer-terms-typo/artifacts"
    assert tab.commands == ()
