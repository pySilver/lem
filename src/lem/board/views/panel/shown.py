"""The task's newest state's line as the panel shows it (`Task.shown` on `main`, printed with
`board_pages.rich`): the board's words for it, with each address of a pull request a link whose
words are the address, as the header's key line and the large card print it."""

import re
from typing import TYPE_CHECKING

from lem.board.views import telling

if TYPE_CHECKING:
    from lem.records.record import Record

# A pull request's link as the card's line makes it, `[#44](URL)`.
NUMBERED = re.compile(r"\[#(\d+)\]\((https?://\S+?/pull/\1)\)")


def shown(record: Record) -> str:
    """The newest state's line, its pull requests linked by their address; "" with none."""
    return NUMBERED.sub(r"[\2](\2)", telling.said(record))


def opening(record: Record) -> str | None:
    """The first line of the state block the card shows."""
    state = telling.newest_state(record.journal)
    return None if state is None else state.opening


def view_href(base: str, view: str) -> str:
    """The address of a view of the workspace: the kanban at its base, `/waits` and the
    others under it."""
    return f"{base}/" if view == "tasks" else f"{base}/{view}"
