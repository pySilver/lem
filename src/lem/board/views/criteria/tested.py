"""What the last check of a criterion's test gave (`board_model.criterion_checks` on `main`):
its problem, that it passes on the branch and fails on the base commit (or that the checks took
that from the polish pass's run, with the pass's commit), or no check yet.

A run counts only for the criteria and tests it ran on: a criterion or a test that changed since
has no check yet.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lem.records.criterion import CriterionTest
    from lem.records.record import Record
    from lem.records.red import RedTest

ENDED = frozenset(("landed", "answered", "dropped"))
SHORT = 7
HELD = "passes on the branch, fails on the base commit"


def runs_of(record: Record) -> dict[tuple[int, str], RedTest]:
    """The tests of the newest check of the criteria, by criterion and command, when it ran
    on the criteria as they are recorded."""
    criteria = record.task.criteria
    red = criteria.red
    if red is None or red.digest != criteria.digest:
        return {}
    return {(test.criterion, test.command): test for test in red.tests}


def taken_of(record: Record) -> dict[int, str]:
    """The criteria whose tests the checks took from the polish pass's run, with the pass's
    commit."""
    checked = record.landing.checked if record.landing else None
    found = checked.criteria if checked else ()
    return {one.criterion: one.taken_at for one in found if one.taken_at}


def said_of(
    record: Record, number: int, test: CriterionTest
) -> tuple[str, bool | None]:
    """What the last check of a test gave, and whether it held the criterion (None with no
    check)."""
    run = runs_of(record).get((number, test.command))
    taken = taken_of(record).get(number)
    if run is not None and run.problem:
        return run.problem, False
    if run is not None:
        return ran_on(record), True
    if taken is not None:
        commit = taken[:SHORT]
        return f"{HELD}, taken from the polish pass at {commit}, not run again", True
    ended = record.task.status in ENDED
    return ("no check of it is on record" if ended else "not checked yet"), None


def ran_on(record: Record) -> str:
    """A test that held its criterion in the newest check, and the commit it ran on."""
    red = record.task.criteria.red
    tip = red.inputs.tip[:SHORT] if red else ""
    return f"{HELD} (checked on {tip})"
