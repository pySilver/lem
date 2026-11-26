"""The current merge authority for the board's pages and server duties."""

from typing import TYPE_CHECKING

from lem.app.owner import merge_bases, read_order
from lem.model.owner import merging
from lem.model.owner.looks import Look, MergeBasis
from lem.records.holds import Parked
from lem.settings.load import settings_of

if TYPE_CHECKING:
    from lem.app.sessions.here import Here
    from lem.records.record import Record


UNKNOWN = MergeBasis()


def parked_reason(record: Record) -> str | None:
    """What the board says in place of a new merge while the task is parked."""
    if not isinstance(record.task.hold, Parked):
        return None
    slug = record.task.slug
    return f"The task is parked. Resume it with /lem resume {slug}."


def bases_of(here: Here, records: tuple[Record, ...]) -> merge_bases.Bases:
    """Read the settings and the current base for this look at the approved tasks."""
    if not any(record.task.status == "open" for record in records):
        return merge_bases.Bases()
    branch = settings_of(here.where.checkout).settings.branch
    return merge_bases.gathered(here, branch, records)


def look(record: Record, basis: MergeBasis) -> Look:
    """The facts that settle who merges, including events within one second."""
    return Look(
        record=record,
        basis=basis,
        read_after_refusal=read_order.after_refusal(record, basis.tree),
    )


def server_merges(record: Record, basis: MergeBasis) -> bool:
    """Whether the current merge belongs to the board server."""
    return merging.merge_wait(look(record, basis)) == merging.MERGES
