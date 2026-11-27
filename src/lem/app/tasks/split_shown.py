"""What `lem task split` prints of each part: its record as it is after the split."""

from typing import TYPE_CHECKING

from lem.records.base import Frozen
from lem.store import tasks

if TYPE_CHECKING:
    from lem.model.task.parts import Part
    from lem.store.places import Workspace


class Made(Frozen, frozen=True, kw_only=True):
    """One part of the split: its slug, its status, the part it waits for, and whether this
    call made its record."""

    slug: str
    status: str
    after: tuple[str, ...] = ()
    made: bool = False


def shown(
    where: Workspace, found: tuple[Part, ...], made: frozenset[str]
) -> tuple[Made, ...]:
    """Each part as its record is now, in the order of the headings."""
    records = (tasks.read(where.state, part.slug).task for part in found)
    return tuple(
        Made(
            slug=task.slug, status=task.status, after=task.after, made=task.slug in made
        )
        for task in records
    )
