"""`lem picker`: agterm's picker over the tasks of the session's repository, and the way to the
task picked: its live session, else its board (`picker.main` on `main`).

An agterm keymap command starts it with a chord; the keymap is agterm's file, and `lem doctor`
gives its line. A pick of a task whose newest session lives with its agent selects that session,
the owner's own act; a task with none, and the last row, open the board server's page of that
task, or of all tasks, as `lem board --follow` does. Nothing is typed into a pane. Escape opens
nothing and says nothing.
"""

from typing import TYPE_CHECKING, Literal

from lem.addons.picker import board, looks, row, sessions
from lem.ports.faults import Unanswered
from lem.records.base import Frozen

if TYPE_CHECKING:
    import datetime as dt
    from pathlib import Path

    from lem.app.sessions.here import Here


class Picked(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """The pick: the task (`:all` for every task), or None for Escape; where it went; and the
    session selected."""

    picked: str | None
    went: Literal["session", "board"] | None = None
    session: str | None = None


def picked(folder: Path, now: dt.datetime) -> Picked:
    """Show the picker, and go to what the owner picked."""
    here, found = looks.listed(folder, now)
    chosen = chosen_row(here, found)
    if chosen is None:
        return Picked(picked=None)
    live = None if chosen == row.ALL else sessions.live_session(here, chosen, now)
    if live is None:
        board.opened(here.where.checkout, chosen)
        return Picked(picked=chosen, went="board")
    try:
        here.ports.terminal.select(live)
    except Unanswered as error:
        raise sessions.unreachable(error) from error
    return Picked(picked=chosen, went="session", session=live)


def chosen_row(here: Here, found: tuple[row.PickRow, ...]) -> str | None:
    """The id of the row the owner picked, None for Escape; refused when agterm cannot show
    the picker."""
    lines = row.lines_of(found)
    try:
        said = here.ports.terminal.picker(tuple(lines), here.where.checkout)
    except Unanswered as error:
        raise sessions.unreachable(error) from error
    return None if said is None else lines[said]
