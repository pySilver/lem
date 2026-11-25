"""One row of Waits for you, for one thing the owner does (`board_pages.wait_article` and
`board_model.wait_say` on `main`): its verb and where it goes, its time, its task and state, its
facts, his acts, and where he answers.

The verb of a row he answers in the task's own session (his step with no answer on the board, a
block, a session that does not answer) jumps to that session on this Mac while it lives.
"""

from typing import TYPE_CHECKING

from lem.board.inputs import clock, names
from lem.board.inputs.waits import Wait
from lem.board.views import offers, sessions, standing, where, words
from lem.board.views.waits import acts, facts, kinds
from lem.model.owner import verbs
from lem.records.holds import OwnerHold

if TYPE_CHECKING:
    from lem.board.inputs.text import View
    from lem.board.views.world import Seen, World
    from lem.model.owner.looks import Row

UNDER: View = "waits"


def wait(world: World, seen: Seen, row: Row, rows: tuple[Row, ...]) -> Wait:
    """The row of `row`, one of the task's `rows`."""
    task = seen.record.task
    said = kinds.said(seen, row)
    verb = verb_of(seen, row)
    told = facts.facts(world, seen, row, verb)
    return Wait(
        id=f"wait-{kinds.key_of(seen, row)}",
        kind=row.kind,
        look=said.look,
        icon=said.icon,
        verb=verb,
        href=href_of(world, seen, row, UNDER),
        jump=jump_of(world, seen, row),
        since=clock.since(row.since, world.clock.now, said.note),
        task=names.title_of(task.slug),
        state=standing.standing(seen, rows).label,
        what=told.what,
        sub=told.sub,
        marks=told.marks,
        reasons=told.reasons,
        acts=acts.acts(world, seen, row),
        where=where.where(seen, row),
    )


def verb_of(seen: Seen, row: Row) -> str:
    """What the owner does, in the board's words: his step says the stage's line."""
    task = seen.record.task
    hold = task.hold
    if row.kind == "held" and isinstance(hold, OwnerHold) and row.say is None:
        return words.capital(words.said(hold.line))
    return verbs.verb(row, task, seen.record.landing)


def href_of(world: World, seen: Seen, row: Row, under: View) -> str:
    """Where the verb goes: the task's panel, a card's own page for a card."""
    tab = kinds.card_tab(row)
    return names.task_href(world.viewer.base, seen.record.task.slug, tab, under)


def jump_of(world: World, seen: Seen, row: Row) -> str | None:
    """The task's session a click on the verb goes to, on this Mac, for a row the owner
    answers there."""
    if not world.viewer.local or not in_session(seen, row):
        return None
    return sessions.jump_of(seen.acts, seen.session)


def in_session(seen: Seen, row: Row) -> bool:
    """Whether the owner answers `row` in the task's own session rather than on the board:
    his step with no answer of the board's, a block, and a session that does not answer."""
    if row.kind == "held":
        return offers.open_question(seen.record.task, "skip") is None
    return (row.kind == "blocked" and row.say is None) or (
        row.kind == "session" and row.deaf
    )
