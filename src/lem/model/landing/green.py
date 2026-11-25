"""Green: the seven conditions under which a pull request says green, in one function
(`landing.md` H 5; `stages/land.md` step 6), each unmet one a reason the pull request names
first (`main:land.not_green`).

The seven: the checks passed with the bar where it was; a review with at least one source left
no must-fix; no criterion changed during the build; nothing of the owner's went past the
personas without him, and no criteria were approved without him; the checks were the main
checkout's own; no read of the criteria went unanswered twice; a task on the fast track is not
careful.
"""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.model.landing import (
    green_checks,
    green_owner,
    green_words,
    propose_criteria,
    review_due,
)
from lem.model.landing.propose_facts import small
from lem.model.landing.review import must_fix, newest, unmet
from lem.records.decisions import CriterionChanged
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.model.landing.world import World
    from lem.records.landing.review import Reviewed
    from lem.records.record import Record

# The personas' reads of the criteria in a row that nobody answered after which the request
# is proposed as not green (`stages/interview.md`, step 5).
SILENT_READS = 2
# The review attempts nobody answered after which the request goes on to the owner as not
# reviewed, and the rounds whose last one may leave a must-fix for him (`stages/land.md`,
# step 5).
SILENT_REVIEWS = 2
ROUNDS = 2
FAST = (
    "careful on the fast track ({0}): it took the fast track, with no interview, no "
    "personas' read of its criterion and no plan, so a person reads it"
)
# What a change of the build did to its criterion, as a reason says it.
CHANGE_HOW = MappingProxyType(
    {"changed": "changed", "added": "was added", "removed": "was removed"}
)


def unread(record: Record) -> tuple[str, ...]:
    """The reason of the personas' read: started twice in a row and nobody answered."""
    reads = propose_criteria.done(record.task)
    if propose_criteria.quiet(reads) < SILENT_READS:
        return ()
    silent = "".join(
        f"; no answer from {source.name} ({source.why})" for source in reads[-1].silent
    )
    started = "the personas' read was started twice and nobody answered"
    return (f"the criteria were not read: {started}{silent}",)


def review(record: Record, world: World | None) -> tuple[str, ...]:
    """The reason of the review: none answered, two attempts after the newest answered one
    nobody answered (`main:land.due_of`), or the newest left a must-fix."""
    landing = record.landing or Landing()
    last = newest(landing)
    if review_due.silent_run(landing) >= SILENT_REVIEWS:
        return ("not reviewed: the review was started twice and no source answered",)
    if last is None:
        return ("no review read the change",)
    coverage = uncovered(record, last, world)
    if coverage:
        return coverage
    count = must_fix(last)
    rounds = [each for each in landing.reviews if each.answered and each.of == "change"]
    if count and len(rounds) >= ROUNDS:
        return (f"two rounds reviewed it: the last one left {count} must-fix",)
    return (f"the review left {count} must-fix",) if count else ()


def uncovered(record: Record, last: Reviewed, world: World | None) -> tuple[str, ...]:
    """The coverage and scope requirements that the latest review did not meet."""
    if world is None:
        return ()
    left = unmet(record, last, world)
    if not left or (len(left) == 1 and must_fix(last)):
        return ()
    joined = ", and ".join(left)
    return (f"the review does not cover this change: {joined}",)


def change_reason(record: Record, change: CriterionChanged) -> str:
    """One change of a criterion as a reason: what it did, and why."""
    how = CHANGE_HOW[change.how]
    why = green_words.change_why(record, change)
    return f"criterion {change.criterion} {how} during the build: {why}"


def changed(record: Record) -> tuple[str, ...]:
    """The reasons of the criteria: each change of the build that no later approval of the
    owner's took over and that his help on a breaker did not make."""
    return tuple(
        change_reason(record, change)
        for change in record.task.decisions
        if isinstance(change, CriterionChanged)
        and green_words.taken_over(record, change) is None
        and not green_words.owners_change(record, change)
    )


def fast(record: Record, careful: tuple[str, ...]) -> tuple[str, ...]:
    """The reason of a careful task on the fast track: a person reads it."""
    if not careful or not small(record):
        return ()
    return (FAST.format(green_words.reason(careful[0])),)


def reasons(
    record: Record, careful: tuple[str, ...], world: World | None = None
) -> tuple[str, ...]:
    """Every reason the pull request is not green, in the order the owner reads them; none
    means green. `careful` is each reason the request is careful (`propose_careful.why`)."""
    landing = record.landing or Landing()
    task = record.task
    found = fast(record, careful) + unread(record)
    found += green_checks.checks(landing) + review(record, world)
    found += green_checks.shown(record) + changed(record)
    return found + green_owner.approval(task) + green_owner.decisions(task)
