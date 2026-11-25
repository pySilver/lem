"""Read each task's base before the server picks its next merge."""

from typing import TYPE_CHECKING

from lem.model.landing import destination, merge_recheck
from lem.settings.load import settings_of

if TYPE_CHECKING:
    from lem.board.duties.context import Duty
    from lem.records.record import Record

type Heads = dict[str | None, str | None]
type Refs = dict[str, str | None]


def ordered(duty: Duty, records: tuple[Record, ...]) -> tuple[Record, ...]:
    """Keep the existing order within each group of passed or stale checks."""
    if not records:
        return ()
    default = settings_of(duty.checkout).settings.branch.base
    refs = {
        record.task.slug: destination.recorded(record.landing) or default
        for record in records
    }
    heads = heads_of(duty, set(refs.values()))
    return tuple(sorted(records, key=lambda one: priority(one, refs, heads)))


def heads_of(duty: Duty, refs: set[str | None]) -> Heads:
    """Read the last fetched head of each destination once."""
    git = duty.here.ports.git
    checkout = duty.checkout
    return {ref: git.remote_head(checkout, ref) for ref in refs if ref}


def priority(record: Record, refs: Refs, heads: Heads) -> bool:
    """The model's order for the current head at this task's destination."""
    ref = refs[record.task.slug]
    return merge_recheck.priority(record, heads.get(ref))
