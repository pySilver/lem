"""A card still belongs to the task's live session, and agterm has no earlier answer."""

from typing import TYPE_CHECKING

from lem.app.asking import live
from lem.app.asking.overlay_read import outcome
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from lem.app.asking.shape import Card


def check(folder: Path, card: Card, environ: Mapping[str, str]) -> None:
    """Check which session asks and whether the owner already answered on the Mac."""
    if not live.current(folder, card.session, environ):
        raise gone()
    told = outcome(environ, card.page)
    if told.kind in ("submitted", "dismissed"):
        raise Refusal(
            "ask-ended-at-mac",
            f"The owner {told.kind} the card in the session.",
            "The session reads its own result.",
        )


def gone() -> Refusal:
    """The live session no longer holds the page."""
    return Refusal(
        "ask-session-gone",
        "The card’s session no longer runs for the task.",
        "The owner can open the current question on the board.",
    )
