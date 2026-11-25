"""The facts of a task's header (`board_task.facts` on `main`): its type and track, its careful
call, what it waits for, its park, then the facts of `places.py`; a fact with nothing to say is
left out."""

from typing import TYPE_CHECKING

from lem.board.inputs.task.head import Fact
from lem.board.views import telling, words
from lem.board.views.panel import places
from lem.board.views.panel.common import careful_of, closed, stamp, track_of
from lem.board.views.panel.waiting import waits_for
from lem.records.holds import Parked

if TYPE_CHECKING:
    from lem.board.views.standing import Standing
    from lem.board.views.world import Seen, World
    from lem.model.owner.looks import Rows

CAREFUL = "careful"


def facts(world: World, seen: Seen, rows: Rows, standing: Standing) -> tuple[Fact, ...]:
    """Every fact of the header of the task of `seen`."""
    found = (
        type_fact(seen),
        careful_fact(seen),
        waits_fact(seen, rows),
        parked_fact(world, seen),
        *places.places(world, seen, standing),
    )
    return tuple(fact for fact in found if fact is not None)


def type_fact(seen: Seen) -> Fact | None:
    """The type of the request and why, with its track."""
    task = seen.record.task
    track, shape = track_of(task), task.shape
    if shape is None:
        return Fact(key="type", term="Type", text=track) if track else None
    why = f"because {shape.why}"
    return Fact(key="type", term="Type", bold=shape.type, text=track, title=why)


def careful_fact(seen: Seen) -> Fact | None:
    """The careful call and why; before one, that the review calls it."""
    record = seen.record
    careful = careful_of(record)
    if careful is not None:
        title = f"{careful.by}: {careful.why}" if careful.why else None
        return Fact(
            key=CAREFUL,
            term="Careful",
            bold="yes" if careful.careful else "no",
            yours=careful.careful,
            sub=careful.why or None,
            title=title,
        )
    if closed(record.task):
        return None
    sub = "the review calls it, before the proposal"
    return Fact(key=CAREFUL, term="Careful", sub=sub)


def waits_fact(seen: Seen, rows: Rows) -> Fact | None:
    """What the task waits for, in the owner's look when it is his, with where he answers
    as its hover."""
    waiting = waits_for(seen, rows)
    if waiting is None:
        return None
    title = f"Where you answer: {waiting.where}" if waiting.where else None
    return Fact(
        key="waits",
        term="Waits for",
        text=waiting.text,
        yours=waiting.yours,
        title=title,
    )


def parked_fact(world: World, seen: Seen) -> Fact | None:
    """Why the owner parked the task, since when, and the line that brings it back."""
    task = seen.record.task
    hold = task.hold
    if not isinstance(hold, Parked):
        return None
    since = stamp(world, hold.since)
    resume = f"/lem resume {task.slug}"
    why = parked_why(seen)
    return Fact(
        key="parked",
        term="Parked",
        text=why,
        title=why,
        sub=f"since {since} · type `{resume}` to bring it back",
    )


def parked_why(seen: Seen) -> str:
    """Why the owner parked a task, its newest state's line, as Waits for you says it."""
    shown = telling.said(seen.record)
    return words.capital(shown) if shown else "No reason is on record."
