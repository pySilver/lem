"""Green: the conditions under which a pull request says green, in one function
(`landing.md` H 5), each unmet one a reason the pull request names.

The plain path checks the checks, the criteria's check, the review's must-fix and careful call,
and the approval. The bar, a changed criterion, a decision taken without an answer, the plan talk
and the persona read are the step `land-propose`'s, with their checks.
"""

from typing import TYPE_CHECKING

from lem.model.landing.review import must_fix, newest
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.records.record import Record


def checks(landing: Landing) -> tuple[str, ...]:
    """The reason of the checks: a run that did not pass."""
    checked = landing.checked
    if checked is None or checked.outcome != "passed":
        return ("the checks did not pass",)
    return ()


def criteria(record: Record) -> tuple[str, ...]:
    """The reasons of the criteria: a test whose fail on the base and pass on the tip nobody
    saw."""
    checked = (record.landing or Landing()).checked
    runs = checked.criteria if checked else ()
    shown = {done.criterion for done in runs if done.red_on_base and done.green_on_tip}
    return tuple(
        f"criterion {criterion.number}'s test was not seen to fail on the base and pass "
        "on the tip"
        for criterion in record.task.criteria.criteria
        if criterion.tests and criterion.number not in shown
    )


def approval(record: Record) -> tuple[str, ...]:
    """The reason of the approval: none, or one the owner did not give."""
    approvals = record.task.criteria.approvals
    if not approvals:
        return ("nobody approved the criteria",)
    if approvals[-1].by == "alone":
        return ("the owner did not approve the criteria: the task ran without him",)
    return ()


def review(landing: Landing) -> tuple[str, ...]:
    """The reasons of the review: a must-fix left, and a careful change."""
    last = newest(landing)
    if last is None:
        return ("no review read the change",)
    left = must_fix(last)
    reasons = [f"the review left {left} must-fix"] if left else []
    if last.careful:
        why = last.careful_why or "the review says so"
        reasons.append(f"the change is careful: {why}")
    return tuple(reasons)


def careful(record: Record) -> tuple[str, ...]:
    """The reason of a request that its shape calls careful: the owner merges it, whatever the
    review's own call (`main:land.merger_refusal`)."""
    shape = record.task.shape
    topics = shape.careful if shape else ()
    return tuple(f"the request is careful: {topic}" for topic in topics)


def reasons(record: Record) -> tuple[str, ...]:
    """Every reason the pull request is not green; none means green."""
    landing = record.landing or Landing()
    found = checks(landing) + criteria(record) + careful(record)
    return found + approval(record) + review(landing)
