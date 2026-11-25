"""The marks a task's spans without the owner fold over (`project.merged` on `main`): the
night's own mark of a task the night opened, and each of his words, in the order of their
moments. In one second the task's mark comes first, and each keeps its own order."""

from typing import TYPE_CHECKING

from lem.model.owner.presence import Said
from lem.records.base import Frozen, Moment

if TYPE_CHECKING:
    from lem.records.owner import Change, Presence
    from lem.records.task import Task


class Mark(Frozen, frozen=True, kw_only=True):
    """One mark of the fold: the task's own (a night's) or one of his words, its moment, and
    whether it says away."""

    at: Moment
    own: bool = False
    away: bool = False
    said: Said


def marks(task: Task, presence: Presence) -> tuple[Mark, ...]:
    """The night's mark of the task, if it has one, and each of his words, in the order of
    their moments, the night's first in one second."""
    found = [*night_marks(task), *map(word_mark, presence.changes)]
    return tuple(sorted(found, key=lambda mark: mark.at))


def night_marks(task: Task) -> tuple[Mark, ...]:
    """The night's mark of a task the night opened, at the moment it began to run alone."""
    night = task.night
    if night is None:
        return ()
    said = Said(by="lem", words=f"the night of {night.isoformat()}")
    return (Mark(at=task.mode_since or task.opened, own=True, said=said),)


def word_mark(change: Change) -> Mark:
    """One of his words as a mark."""
    said = Said(by="owner", words=change.words)
    return Mark(at=change.at, away=change.away, said=said)
