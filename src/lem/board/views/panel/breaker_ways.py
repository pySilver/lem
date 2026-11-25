"""Where the owner answers a breaker on its card (`board_task.breaker_card` on `main`): while it
waits, his Help, Park and Drop here where the page may act, the Inbox's line or the session's,
and the lines he types; while the task is parked, that the breaker waits for nobody."""

from typing import TYPE_CHECKING, NamedTuple

from lem.board.views import answering, offers
from lem.board.views.panel import inbox, lines, ways
from lem.board.views.panel.answer import answer
from lem.records.holds import BreakerHold, Parked

if TYPE_CHECKING:
    from lem.board.inputs.forms import AnswerForm, Way
    from lem.board.views.world import Seen, World
    from lem.model.owner.looks import Rows
    from lem.records.task import Task

PARKED = "The task is parked: this breaker waits for nobody until you bring it back."


class Asks(NamedTuple):
    """Where the owner answers a breaker, his answer here, and the ways beside it."""

    where: str | None = None
    answer: AnswerForm | None = None
    ways: tuple[Way, ...] = ()


def asks(world: World, seen: Seen, rows: Rows) -> Asks:
    """Where the owner answers the breaker of the task of `seen`."""
    task = seen.record.task
    typed = lines.owner_lines(task)
    if not isinstance(task.hold, BreakerHold):
        return Asks(where=resting(task), ways=typed)
    form = form_of(world, seen)
    found = ways.inbox_ways(world, seen, rows) or ways.session_ways(world, seen)
    return Asks(
        where=where_of(world, task.slug, rows, here=form is not None),
        answer=form,
        ways=(*found, *typed),
    )


def form_of(world: World, seen: Seen) -> AnswerForm | None:
    """His Help, Park and Drop here, where the page may act and until his answer is on
    record."""
    asked = offers.open_question(seen.record.task, "breaker")
    if asked is None:
        return None
    return answering.form(world, asked, "panel", world.viewer.view)


def resting(task: Task) -> str:
    """Where a breaker that waits for nobody is answered: nowhere while the task is
    parked, else where the task says."""
    return PARKED if isinstance(task.hold, Parked) else answer(task)


def where_of(world: World, slug: str, rows: Rows, *, here: bool) -> str | None:
    """Where he answers: here and in the session, or in the session alone; None while the
    Inbox's line says both places."""
    said = inbox.inbox_of(world, slug, rows)
    if said is not None and said.asks:
        return None
    if here:
        return "help, park or drop it here, or help in the task’s session."
    return "help in the task’s session."
