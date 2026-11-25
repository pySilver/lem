"""A landing step's result and what the record and world say is due after it."""

from typing import TYPE_CHECKING

import msgspec

from lem.app.landing import say
from lem.app.landing.world import gather
from lem.kernel.envelope import Envelope
from lem.model.landing import phases
from lem.records.journal.landing import CheckEnd
from lem.store import tasks

if TYPE_CHECKING:
    from lem.app.landing.frame import Context
    from lem.model.landing.world import Due, Verb
    from lem.records.record import Record


def looked(context: Context, record: Record | None = None) -> Due:
    """The due step after the act, from the record and the world as they are now."""
    slug, now = context.record.task.slug, context.world.now
    current = record or tasks.read(context.workspace.state, slug)
    world = gather(context.ports, context.workspace, current, now, fetch=False)
    return phases.due(current, world)


def check_line(before: Record, after: Record) -> str:
    """The completion line the checks just wrote to the journal."""
    added = after.journal[len(before.journal) :]
    end = next(entry for entry in reversed(added) if isinstance(entry, CheckEnd))
    return end.say


def finished(context: Context, verb: Verb, made: object) -> Envelope:
    """The step's result, its line for a run of the checks, and what comes next."""
    outcome = msgspec.Raw(msgspec.json.encode(made))
    slug = context.record.task.slug
    record = tasks.read(context.workspace.state, slug)
    following = say.following(slug, looked(context, record))
    line = check_line(context.record, record) if verb == "checks" else None
    return Envelope(ok=True, outcome=outcome, say=line, following=following)
