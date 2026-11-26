"""The Activity line of a set of criteria as the lead records it."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel import clock
from lem.records.journal.task import CriteriaNoted

if TYPE_CHECKING:
    from lem.app.decisions.writing import Change
    from lem.model.criteria.standing import Shown
    from lem.records.record import Record


def recorded(record: Record, *, kept: Change, seen: Shown) -> Record:
    """Keep the criteria and their Activity line in the same write."""
    changed = kept(record)
    noted = CriteriaNoted(
        at=clock.now(), event="recorded", size=seen.size, number=len(seen.criteria)
    )
    return replace(changed, journal=(*changed.journal, noted))
