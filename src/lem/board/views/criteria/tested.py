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


def run_of(record: Record, number: int, test: CriterionTest) -> RedTest | None:
    """The newest check of this exact test on the criteria as recorded."""
    criteria = record.task.criteria
    red = criteria.red
    if red is None or not red.digest or red.digest != criteria.digest:
        return None
    found = (
        run
        for run in red.tests
        if (run.criterion, run.command, run.files) == (number, test.command, test.files)
    )
    return next(found, None)


def taken_of(record: Record, number: int) -> str | None:
    """The polish commit when the checks took the recorded run of this criterion."""
    checked = record.landing.checked if record.landing else None
    red = record.task.criteria.red
    if checked is None or red is None or checked.at < red.at:
        return None
    tip = red.inputs.tip
    return next(
        (
            tip
            for one in checked.criteria
            if one.criterion == number
            and one.taken_at == tip
            and one.green_on_tip
            and one.red_on_base
        ),
        None,
    )


def said_of(
    record: Record, number: int, test: CriterionTest
) -> tuple[str, bool | None]:
    """What the last check of a test gave, and whether it held the criterion (None with no
    check)."""
    run = run_of(record, number, test)
    if run is None:
        ended = record.task.status in ENDED
        return ("no check of it is on record" if ended else "not checked yet"), None
    if run.problem:
        return run.problem, False
    return ran_on(record, number), True


def ran_on(record: Record, number: int) -> str:
    """A test that held its criterion in the newest check, and the commit it ran on."""
    red = record.task.criteria.red
    tip = red.inputs.tip[:SHORT] if red else ""
    if taken_of(record, number) is not None:
        return f"{HELD}, taken from the polish pass at {tip}, not run again"
    return f"{HELD} (checked on {tip})"
