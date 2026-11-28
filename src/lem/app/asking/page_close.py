"""Close one question page in one agterm session, while that session's overlay still shows it.

The command line and the board server both close a card's page through here: the session's
waiter when it reads the board's answer, and the server as soon as the board's answer is the
first one. `agtermctl session overlay close` names a session and no page, so the tree is read
first: the second of two closes finds no page and closes nothing.

The server matches the page by its id alone. Its temporary folder can differ from the
session's, so the folder of the page's file says nothing to it; the id is the card's page id,
which only that card has.
"""

from typing import TYPE_CHECKING

from lem.app.asking import overlay_read, overlay_tree
from lem.ports.faults import Unanswered

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

TARGET = "--target"


def by_id(overlays: tuple[overlay_tree.Overlay, ...], page: str) -> bool:
    """The session shows the page with this id, wherever its file is."""
    return any(overlay.id == page for overlay in overlays)


def close(
    environ: Mapping[str, str],
    session: str,
    page: str,
    *,
    shows: Callable[[tuple[overlay_tree.Overlay, ...], str], bool] = by_id,
) -> bool:
    """Close the session's overlay while it shows this page; False when it shows another
    page or none."""
    if not shows(overlay_tree.read(environ, session), page):
        return False
    told = overlay_read.reply(environ, "close", TARGET, session)
    if not told.ok or told.error:
        raise Unanswered("agtermctl", told.error or "the question page did not close")
    return True
