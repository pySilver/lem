"""The breaker's document on a task's Overview (`board_task.breaker_card` on `main`): first while
it waits, for the owner or, while the task is parked, for nobody; its markdown as Artifacts
renders it, its links, where he answers, his Help, Park and Drop here, and the ways to the
session, the Inbox and the lines he types."""

from typing import TYPE_CHECKING

from lem.board.inputs import clock
from lem.board.inputs.task.cards import Breaker
from lem.board.views import hovers, words
from lem.board.views.panel import breaker_parts, breaker_ways
from lem.board.views.panel.common import stamp
from lem.board.views.panel.review import artifact
from lem.board.views.panel.stopped import stopped
from lem.records.holds import BreakerHold

if TYPE_CHECKING:
    from lem.board.views.world import Seen, World
    from lem.model.owner.looks import Rows


def breaker(world: World, seen: Seen, rows: Rows) -> Breaker | None:
    """The card of the breaker that stopped the task of `seen`, or None."""
    task = seen.record.task
    found = stopped(task)
    if found is None:
        return None
    name = found.document or "breaker.md"
    text = seen.text(name)
    asks = breaker_ways.asks(world, seen, rows)
    return Breaker(
        waits=isinstance(task.hold, BreakerHold),
        head=f"The build stopped · breaker {found.id}",
        why=words.capital(hovers.stop_words(found)),
        at=clock.since(found.at, world.clock.now, stamp(world, found.at)),
        document=breaker_parts.document_of(world, seen, found, text),
        missing=breaker_parts.missing(name) if text is None else None,
        artifact=artifact(world, task.slug, name),
        handoff=breaker_parts.handoff(world, seen, found),
        where=asks.where,
        answer=asks.answer,
        ways=asks.ways,
    )
