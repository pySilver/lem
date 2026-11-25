"""The reasons of green that the checks give (`main:land.not_green`): commands the branch
brought, a run that did not pass, a lowered bar with the builder's reason and the review's
answer, and a criterion whose test nobody saw fail on the base and pass on the tip."""

from typing import TYPE_CHECKING

from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.records.landing.checks import Checked, Lowered
    from lem.records.record import Record

NOT_PASSED = "the checks did not pass"


def own(checked: Checked) -> tuple[str, ...]:
    """The reason of checks the change brought: the main checkout names none, so every
    later task is checked by these."""
    if not checked.own_checks:
        return ()
    named = ", ".join(f"`{outcome.command}`" for outcome in checked.outcomes)
    return (
        (
            "the checks came with this change: the main checkout's settings name no "
            f"command of the checks, and the branch's .lem/settings.toml brings {named}. "
            "Read the checks once: every later task is checked by them"
        ),
    )


def lowered_line(lowered: Lowered) -> str:
    """A lowered bar as a reason: the file and how, the builder's reason, the review's
    answer or that no review said anything of it."""
    builder = lowered.reason or "no reason given."
    said = lowered.reviewer
    answer = f"The review: {said}" if said else "No review said anything of it."
    where = f"`{lowered.path}` ({lowered.how})"
    return f"the bar is lower in {where}. The builder: {builder} {answer}"


def checks(landing: Landing) -> tuple[str, ...]:
    """The reasons of the checks: the branch's own commands, a run that did not pass, and
    each lowered bar."""
    checked = landing.checked
    if checked is None:
        return (NOT_PASSED,)
    passed = () if checked.outcome == "passed" else (NOT_PASSED,)
    lowered = tuple(map(lowered_line, checked.lowered))
    return own(checked) + passed + lowered


def shown(record: Record) -> tuple[str, ...]:
    """A criterion with a test that nobody saw fail on the base and pass on the tip."""
    checked = (record.landing or Landing()).checked
    runs = checked.criteria if checked else ()
    seen = {done.criterion for done in runs if done.red_on_base and done.green_on_tip}
    return tuple(
        f"criterion {criterion.number}'s test was not seen to fail on the base and pass "
        "on the tip"
        for criterion in record.task.criteria.criteria
        if criterion.tests and criterion.number not in seen
    )
