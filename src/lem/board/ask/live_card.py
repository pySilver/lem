"""A card still belongs to the task's live session, and agterm has no earlier answer."""

from typing import TYPE_CHECKING

from lem.app.sessions import log
from lem.app.wiring import bound
from lem.board.ask.overlay_read import outcome
from lem.kernel import paths
from lem.kernel.errors import Refusal
from lem.ports.place import Place
from lem.ports.terminal import Unreadable

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from lem.board.ask.shape import Card


def check(folder: Path, card: Card, environ: Mapping[str, str]) -> None:
    """Check which session asks and whether the owner already answered on the Mac."""
    current(folder, card.session, environ)
    told = outcome(environ, card.page)
    if told.kind in ("submitted", "dismissed"):
        raise Refusal(
            "ask-ended-at-mac",
            f"The owner {told.kind} the card in the session.",
            "The session reads its own result.",
        )


def current(folder: Path, session: str, environ: Mapping[str, str]) -> None:
    """Reject an older session's card, or a session missing from agterm's list."""
    newest = log.newest_open(log.read(folder))
    if newest is None or not log.same(newest.session, session):
        raise gone()
    checkout = folder.parents[3]
    place = Place(checkout=checkout, home=paths.home(environ), environ=environ)
    terminal = bound(place).terminal
    panes = terminal.sessions()
    if isinstance(panes, Unreadable):
        raise Refusal(
            "ask-session-unreadable", panes.why, "The owner can use the session."
        )
    if not any(log.same(pane.id, session) for pane in panes):
        raise gone()


def gone() -> Refusal:
    """The live session no longer holds the page."""
    return Refusal(
        "ask-session-gone",
        "The card’s session no longer runs for the task.",
        "The owner can open the current question on the board.",
    )
