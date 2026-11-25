"""The current merge authority for the board's pages and server duties."""

from typing import TYPE_CHECKING

from lem.app.owner import looking, read_order
from lem.model.owner import merging
from lem.model.owner.looks import Look, MergeBasis
from lem.settings.load import settings_of

if TYPE_CHECKING:
    from lem.app.sessions.here import Here
    from lem.records.record import Record


def basis_of(here: Here, records: tuple[Record, ...]) -> MergeBasis:
    """Read the settings and the current base for this look at the approved tasks."""
    if not any(record.task.status == "open" for record in records):
        return MergeBasis()
    branch = settings_of(here.where.checkout).settings.branch
    return looking.basis_of(here, branch, records)


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
