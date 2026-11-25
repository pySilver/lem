"""A task's decisions as one record: the next number, the write of one more, and each as it
stands now (`decisions.Task` on `main`).

A decision, a criterion's change and a breaker share one row of numbers, so "decision 3" and
"breaker 4" never name the same line. A task that ended (dropped, landed or answered) takes no
write: nobody builds it, so nothing of it is decided or waits any more, and its record stays as
it ended. A breaker waits until the owner's help settles it, a decision that names it.
"""

from typing import TYPE_CHECKING, Literal

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.records.base import Frozen, Moment
from lem.records.decisions import Breaker, Decision, Taken
from lem.records.journal.task import DecisionNoted

if TYPE_CHECKING:
    from datetime import datetime

    from lem.records.record import Record
    from lem.records.task import Task

ENDED = frozenset(("dropped", "landed", "answered"))
type State = Literal["taken", "waits", "helped"]


class Listed(Frozen, frozen=True, kw_only=True):
    """A decision or a breaker as it stands now: a breaker waits, or the owner's help, decision
    `help` at `helped`, settled it."""

    decision: Decision
    state: State
    help: int | None = None
    helped: Moment | None = None


def writable(task: Task) -> None:
    """Refuse a write to a task that ended."""
    if task.status not in ENDED:
        return
    raise Refusal(
        "ended",
        f"{task.slug} is {task.status}: nothing of it is decided or waits any more, so this "
        "is not written",
        f"its record stays as it is (lem decisions list {task.slug}); new work is a new ask",
    )


def added(record: Record, decision: Decision, now: datetime) -> Record:
    """The record with one more decision, and its line in the journal."""
    task = record.task
    writable(task)
    noted = DecisionNoted(at=now, id=decision.id, what=decision.kind)
    decisions = (*task.decisions, decision)
    return replace(
        record,
        task=replace(task, decisions=decisions),
        journal=(*record.journal, noted),
    )


def helps(task: Task) -> dict[int, Taken]:
    """The owner's help on each breaker that has one, by the breaker's number."""
    taken = (one for one in task.decisions if isinstance(one, Taken))
    return {one.breaker: one for one in taken if one.breaker is not None}


def one_listed(decision: Decision, helped: dict[int, Taken]) -> Listed:
    """One decision or breaker as it stands now."""
    if not isinstance(decision, Breaker):
        return Listed(decision=decision, state="taken")
    help_of = helped.get(decision.id)
    if help_of is None:
        return Listed(decision=decision, state="waits")
    return Listed(decision=decision, state="helped", help=help_of.id, helped=help_of.at)


def listed(task: Task) -> tuple[Listed, ...]:
    """Each decision and breaker of the task as it stands now."""
    helped = helps(task)
    return tuple(one_listed(decision, helped) for decision in task.decisions)


def waiting(task: Task) -> tuple[Breaker, ...]:
    """The breakers of the task that wait for the owner's help."""
    helped = helps(task)
    breakers = (one for one in task.decisions if isinstance(one, Breaker))
    return tuple(one for one in breakers if one.id not in helped)
