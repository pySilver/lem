"""The breakers that wait for the owner (`decisions.cmd_pending` on `main`): of one task or of
every task. A parked task's wait for nobody now; a dropped, landed or answered task has none
waiting, since nobody builds it, and its breakers are named under `ended`."""

from typing import TYPE_CHECKING

from lem.model.decisions import book
from lem.records.base import Frozen
from lem.records.decisions import Breaker
from lem.records.holds import Parked

if TYPE_CHECKING:
    from lem.records.task import Task


class Waits(Frozen, frozen=True, kw_only=True):
    """A breaker that waits, its task and the task's status."""

    task: str
    status: str
    breaker: Breaker


class Ended(Frozen, frozen=True, kw_only=True):
    """A task that ended with breakers that waited, or the one named."""

    task: str
    status: str
    breakers: tuple[int, ...] = ()
    says: str


class Pending(Frozen, frozen=True, kw_only=True):
    """The breakers that wait, those of parked tasks, and the tasks that ended."""

    waiting: tuple[Waits, ...] = ()
    parked: tuple[Waits, ...] = ()
    ended: tuple[Ended, ...] = ()


def ended_of(task: Task, breakers: tuple[Breaker, ...]) -> Ended:
    """A task that ended, with the breakers that no longer wait for anybody."""
    return Ended(
        task=task.slug,
        status=task.status,
        breakers=tuple(one.id for one in breakers),
        says=f"the task is {task.status}: its breakers no longer wait for anybody",
    )


def waits_of(task: Task) -> tuple[Waits, ...]:
    """The breakers of a task that has not ended, each with its task."""
    return tuple(
        Waits(task=task.slug, status=task.status, breaker=one)
        for one in book.waiting(task)
    )


def pending(tasks: tuple[Task, ...], *, named: bool) -> Pending:
    """The breakers of `tasks` that wait, by where they wait; `named` keeps an ended task with
    none."""
    going = [task for task in tasks if task.status not in book.ENDED]
    ended = (
        ended_of(task, book.waiting(task))
        for task in tasks
        if task.status in book.ENDED
    )
    return Pending(
        waiting=tuple(
            one for task in going if not parked(task) for one in waits_of(task)
        ),
        parked=tuple(one for task in going if parked(task) for one in waits_of(task)),
        ended=tuple(one for one in ended if one.breakers or named),
    )


def parked(task: Task) -> bool:
    """Whether his park holds the task."""
    return isinstance(task.hold, Parked)
