"""The refusals of `propose` that the build leaves (`main:land.cmd_propose`): the task's own
backlog item still on its branch, a plan talk its plan called for and nobody held, a breaker
that waits for the owner, a careful change that did not get the full set, and a title that is
not one line."""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.landing import (
    propose_criteria,
    propose_doubts,
    propose_filed,
)
from lem.model.landing.invariants import protected
from lem.model.landing.review import newest
from lem.records.decisions import Breaker, Taken
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.model.landing.propose_facts import Facts
    from lem.model.landing.world import World
    from lem.records.record import Record

# A plan of more tasks than this is large: a plan talk before any code. The three-touches
# plan's own line (2026-11-15), not a measurement.
LARGE_AFTER = 3


def own_item(record: Record, facts: Facts) -> Refusal | None:
    """A task started from a backlog item did that item's work, so its branch removes the
    item, and the merge takes it off the base and off the board."""
    own, slug = record.task.backlog_item, record.task.slug
    if own is None or own not in facts.in_tip:
        return None
    return Refusal(
        "own-item",
        f"{slug} was started from the backlog item {own} (its ask is that path), and the "
        "branch still holds it: the task does that item's work, so its branch removes it",
        f"a builder removes it in the task's worktree in a commit of its own (git rm -q -- "
        f"{own}, then a commit in the project's message form), then lem land checks "
        f"{slug} and this step run again; the review that read the change still covers it",
    )


def talk_due(record: Record) -> str | None:
    """Why the request's plan had to be talked through before any code: its own careful
    call, or more than three tasks. None when it did not, the fast track's too: the owner's
    later word or the review's call gives the full set and his merge, and no talk."""
    plan = record.task.plan
    if plan is None:
        return None
    if plan.careful:
        return "the plan says that the request is careful"
    tasks = plan.tasks or 0
    if plan.large or tasks > LARGE_AFTER:
        return f"the plan has {tasks} tasks, more than three"
    return None


def untalked(record: Record) -> Refusal | None:
    """A careful or large plan is talked through by its defender and the reviewer before
    any code; a request with no talk on record skipped that step."""
    due, slug = talk_due(record), record.task.slug
    if due is None or record.task.talk is not None:
        return None
    return Refusal(
        "plan-talk",
        f"{due}, so its defender and the reviewer talk its plan through in the plan talk's "
        f"companion before any code (stages/talk.md), and {slug} has no plan talk on record",
        f"the task goes back to its build as planned, with needs a session: {due}; its "
        f"lead holds the talk, and its defender records it with lem task talked {slug}",
    )


def waiting(record: Record) -> Refusal | None:
    """A request is never proposed over a breaker that stopped its build and that the owner
    did not help on."""
    task = record.task
    helped = {
        decision.breaker
        for decision in task.decisions
        if isinstance(decision, Taken) and decision.by == "owner"
    }
    stopped = [
        found
        for found in task.decisions
        if isinstance(found, Breaker) and found.id not in helped
    ]
    if not stopped:
        return None
    first = stopped[0]
    return Refusal(
        "breaker",
        f"breaker {first.id} of {task.slug} waits for the owner ({first.what}): its build "
        "stopped there, and a request is never proposed over it",
        f"the owner reads its document and helps (lem decisions log {task.slug} --by owner "
        f"--breaker {first.id} ...), parks the task or drops it",
    )


def titled(title: str) -> Refusal | None:
    """The title is one line: the subject of the change."""
    if title.strip() and "\n" not in title:
        return None
    return Refusal(
        "title",
        "--title is one line: the subject of the change",
        "give the report's commit subject as --title",
    )


def floor(record: Record, *, careful: bool) -> Refusal | None:
    """A careful request gets the project's full set, whatever made it careful after its
    review began: an edit of Lem's own settings too (`main:land.due_of`)."""
    last = newest(record.landing or Landing())
    if last is None or last.kind == "full" or not careful:
        return None
    slug = record.task.slug
    return Refusal(
        "review-floor",
        f"the request is careful, and its newest review was {last.kind}: a careful change "
        "gets the project's full set",
        f"lem land read {slug} says what a reviewer gets; run the full set, then record it "
        f"with lem land read {slug} --record FILE",
    )


def gates(
    record: Record, world: World, facts: Facts, *, careful: bool
) -> Refusal | None:
    """The first gate of the build the request does not pass, or None."""
    found = (
        protected(world.branch, world.rules, "pushes"),
        own_item(record, facts),
        untalked(record),
        propose_criteria.unread(record),
        propose_criteria.silent(record),
        propose_doubts.doubted(record),
        propose_doubts.unapproved(record),
        propose_filed.gone(record, facts),
        propose_filed.refuted(record, facts),
        waiting(record),
        floor(record, careful=careful),
    )
    return next((refusal for refusal in found if refusal is not None), None)
