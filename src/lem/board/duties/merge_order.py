"""Read each task's base before the server picks its next merge."""

from typing import TYPE_CHECKING

from lem.model.landing import merge_recheck

if TYPE_CHECKING:
    from lem.app.owner.merge_bases import Bases
    from lem.records.record import Record


def ordered(bases: Bases, records: tuple[Record, ...]) -> tuple[Record, ...]:
    """Keep the existing order within each group of passed or stale checks."""
    return tuple(
        sorted(
            records,
            key=lambda one: merge_recheck.priority(one, bases.for_task(one).base),
        )
    )
