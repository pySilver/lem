"""A card still belongs to the task's live session, and agterm has no earlier answer."""

from typing import TYPE_CHECKING

from lem.app.owner.sessions import agent_is_live
from lem.app.sessions import agents, beside, log
from lem.app.wiring import bound
from lem.board.ask.overlay_read import outcome
from lem.kernel import paths
from lem.kernel.errors import Refusal
from lem.ports.place import Place

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from lem.board.ask.shape import Card
    from lem.ports.terminal import Terminal


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
    """Reject an older session's card, or a session without a running agent."""
    newest = log.newest_open(log.read(folder))
    if newest is None or not log.same(newest.session, session):
        raise gone()
    checkout = folder.parents[3]
    place = Place(checkout=checkout, home=paths.home(environ), environ=environ)
    if not running(bound(place).terminal, session):
        raise gone()


def running(terminal: Terminal, session: str) -> bool:
    """Check the agent in the named pane from one terminal read."""
    grounds = beside.looks(terminal).foregrounds()
    for pane, words in grounds.items():
        if log.same(pane, session):
            return agent_is_live(listed=True, agent=agents.agent_runs(words))
    return False


def gone() -> Refusal:
    """The live session no longer holds the page."""
    return Refusal(
        "ask-session-gone",
        "The card’s session no longer runs for the task.",
        "The owner can open the current question on the board.",
    )
