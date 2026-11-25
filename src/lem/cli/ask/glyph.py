"""The mark of a question in the sidebar of its own session."""

import sys
from typing import TYPE_CHECKING

from lem.adapters import agterm_ctl
from lem.board.ask.overlay_read import environment
from lem.ports.faults import Unanswered

if TYPE_CHECKING:
    from lem.cli.ask.overlay import Overlay


def set_mark(overlay: Overlay, words: tuple[str, ...]) -> None:
    """Set the question's mark, with a line when this courtesy fails."""
    try:
        mark(overlay, words)
    except (OSError, Unanswered) as error:
        sys.stderr.write(f"lem ask could not set the question's status: {error}\n")


def mark(overlay: Overlay, words: tuple[str, ...]) -> None:
    """Set one status on the pane that asked."""
    environ = overlay.environ
    pane = environ.get("AGTERM_PANE_ID")
    extra = ("--pane-id", pane) if pane else ()
    agterm_ctl.said(
        environment(environ),
        "session",
        "status",
        *words,
        "--target",
        overlay.session,
        *extra,
    )
