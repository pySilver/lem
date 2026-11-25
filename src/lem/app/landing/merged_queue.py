"""Write the answer to a merge call that the forge queued."""

from typing import TYPE_CHECKING

from lem.app.landing import reconcile
from lem.kernel.errors import Refusal
from lem.model.landing import reconcile_queue
from lem.records.landing.merge import MergeAccepted

if TYPE_CHECKING:
    from lem.app.landing.frame import Context


def recorded(context: Context) -> MergeAccepted:
    """Record the queue's answer for an open pull request, or refuse with what it shows."""
    record, world = context.record, context.world
    intent = record.landing.intent if record.landing else None
    if intent is None:
        found = reconcile_queue.queued(record, world)
    else:
        found = reconcile_queue.answer(record, world, intent)
    if isinstance(found, Refusal):
        raise found
    if isinstance(found, MergeAccepted):
        reconcile.written(context, record, found, found.by or "owner")
        return found
    raise reconcile.refused(context, record, found)
