"""The cards above a task's large card that the owner answers or answered (`board_task.
cards_card`, `parked_card` and `answered_card` on `main`): each `lem-ask` card of its live
session, a park with its why, and his answer on record that its session has not taken yet."""

from typing import TYPE_CHECKING

from lem.board.inputs import clock
from lem.board.inputs.names import plural, task_href
from lem.board.inputs.parts import Link
from lem.board.inputs.task.cards import Asked
from lem.board.inputs.task.overview import Put
from lem.board.views import words
from lem.board.views.panel.common import stamp
from lem.board.views.panel.facts import parked_why
from lem.records.holds import Parked

if TYPE_CHECKING:
    from lem.board.views.world import Seen, World
    from lem.model.owner.looks import Row, Rows


def cards(world: World, rows: Rows) -> tuple[Asked, ...]:
    """Each card the task's live session waits on, from its rows of what waits."""
    asked = (row for row in rows if row.kind == "card")
    return tuple(card(world, row) for row in asked if row.card)


def card(world: World, row: Row) -> Asked:
    """One card: its prompt, since when, and the way to answer it here."""
    page = page_of(row.card or "")
    link = None
    if world.viewer.may_act:
        tab = f"card/{page}"
        href = task_href(world.viewer.base, row.task, tab, world.viewer.view)
        link = Link(
            href=href, label="Answer the card…", icon="user", press="go", frame=True
        )
    prompt = words.capital(row.prompt or "The task’s session asks you")
    return Asked(
        page=page,
        prompt=prompt,
        link=link,
        since=clock.since(row.since, world.clock.now),
    )


def page_of(card: str) -> str:
    """The card's page: the last part of its question's id (`card:SLUG:PAGE`)."""
    return card.rpartition(":")[2]


def cards_said(count: int) -> str | None:
    """`1 card waits for your answer`, or None with none."""
    if not count:
        return None
    waits = "waits" if count == 1 else "wait"
    return f"{plural(count, 'card')} {waits} for your answer"


def parked(world: World, seen: Seen) -> Put | None:
    """A parked task's first line: since when, why in the owner's words, and the line that
    brings it back."""
    task = seen.record.task
    hold = task.hold
    if not isinstance(hold, Parked):
        return None
    return Put(
        since=stamp(world, hold.since),
        why=parked_why(seen),
        resume=f"/lem resume {task.slug}",
    )
