"""The board server closes a card's page in the card's own session, after the board's answer.

The server does it as soon as the board's answer is the first one, so the page closes also when
no wait for it runs: after `lem ask ask --no-wait`, or after a wait that ended `pending`. A
waiter that still runs reads the same answer and finds the page closed, or closes it first.

A failed close leaves the answer on record and the owner's reply as it is. Its fault goes to
the server's `lem.log`, with the page id and the reason.
"""

from typing import TYPE_CHECKING

from lem.app.asking import page_close
from lem.board import opening, update
from lem.kernel.errors import Fault
from lem.ports.faults import Unanswered

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path


class Unclosed(Fault):
    """The card's page stayed open in its session after the board's answer."""

    def __init__(self, page: str, session: str, error: Exception) -> None:
        """Name the page, its session and the reason, and keep the reason's traceback."""
        super().__init__(
            f"the board kept the owner's answer, and the page {page} did not close "
            f"in session {session}: {error}"
        )
        self.__cause__ = error


def close(home: Path, session: str, page: str, environ: Mapping[str, str]) -> None:
    """Leave the caller's window, as the server does before it reads the terminal, and close
    the page while the session's overlay still shows it."""
    detached = dict(environ)
    opening.detached(detached)
    try:
        page_close.close(detached, session, page)
    except (OSError, Unanswered) as error:
        update.logged(home, Unclosed(page, session, error))
