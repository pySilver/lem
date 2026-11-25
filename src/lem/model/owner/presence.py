"""Whether a task runs without the owner now, and which of a workspace's tasks his away or his
back changes (`project.cmd_owner` on `main`).

His away and his back are the machine's (`owner.json` in Lem's home folder): his word in any
repository holds in every one, and a repository has none of its own. A night's task runs
without him from its open until it ends, whatever his status says: his back never brings it
back to him.
"""

from typing import TYPE_CHECKING

from lem.records.base import Frozen, Moment

if TYPE_CHECKING:
    from lem.records.owner import Presence
    from lem.records.task import Task

ENDED = frozenset(("landed", "answered", "dropped"))


class Said(Frozen, frozen=True, kw_only=True):
    """Who began or ended a span without him, and in which words: his own, or Lem's for a
    night."""

    by: str
    words: str | None = None


class Without(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """One span in which a task ran without the owner: from, to (None while it runs), and the
    words that began and ended it."""

    start: Moment
    end: Moment | None = None
    started: Said
    ended: Said | None = None


def alone(task: Task, presence: Presence) -> bool:
    """Whether the task runs without the owner now: a night's task, or he is away."""
    return task.night is not None or presence.away


def going(tasks: tuple[Task, ...]) -> tuple[Task, ...]:
    """The tasks that did not end."""
    return tuple(task for task in tasks if task.status not in ENDED)


def changed(
    tasks: tuple[Task, ...], before: Presence, after: Presence
) -> tuple[str, ...]:
    """The tasks his word changed, by name: after an away, every task that runs without him
    now; after a back, each that ran without him and is his again, which a night's never is,
    and none when he was there already."""
    if after.away:
        return tuple(task.slug for task in going(tasks))
    if not before.away:
        return ()
    return tuple(task.slug for task in going(tasks) if task.night is None)
