"""The order the owner sees when a base refusal and a merge read share a second."""

from typing import TYPE_CHECKING

from lem.model.landing import mergeread
from lem.records.journal.merge import ReadNoted, RefusalNoted

if TYPE_CHECKING:
    from lem.records.landing.merge import Refused
    from lem.records.landing.propose import MergeRead
    from lem.records.record import Record


def after_refusal(record: Record, base_tree: str | None = None) -> bool | None:
    """Whether the settled read with no verdict follows the base refusal on record."""
    landing = record.landing
    if record.task.status != "open" or landing is None or landing.refused is None:
        return None
    refused = landing.refused
    if (refused.source, refused.kind) != ("lem", "base"):
        return None
    read = mergeread.latest(landing, base_tree)
    if read is None or read.verdict is not None or read.tip != refused.tip:
        return None
    return order_of(record, refused, read)


def order_of(record: Record, refused: Refused, read: MergeRead) -> bool | None:
    """Compare their notes in the journal, which keeps the order within a second."""
    after = False
    for entry in reversed(record.journal):
        if isinstance(entry, RefusalNoted) and entry.refusal == refused:
            return after
        if isinstance(entry, ReadNoted) and entry.read == read:
            after = True
    return None
