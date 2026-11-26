"""Restore the door's setting only when the start refuses it."""

import tomllib
from dataclasses import replace
from typing import TYPE_CHECKING

from lem.board import ensure
from lem.kernel import locks, paths
from lem.kernel.errors import Refusal
from lem.settings import edit, lines, reading
from lem.settings.write import Asked, checkout_of, edit_for

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from lem.board.facts import Shown

# These outcomes establish that this attempt did not start a server with the door.
REFUSALS = (
    "port-held",
    "other-home",
    "owner-port",
    "server-start",
    "stop-refused",
    "stop-late",
    "door-not-open",
)


def opened(asked: Asked) -> Shown:
    """Give the child its startup setting and restore that key on refusal."""
    where = reading.Where(
        checkout=checkout_of(asked.folder, asked.scope),
        home=paths.home(asked.environ),
        environ=asked.environ,
    )
    change = edit_for(asked, where)
    with locks.held(change.lock):
        before = previous(change)
        edit.written(change, where)
        try:
            return confirmed(asked.environ, asked.folder)
        except Refusal as refused:
            if refused.code in REFUSALS:
                edit.written(before, where)
            raise


def previous(change: edit.Edit) -> edit.Edit:
    """The edit that restores the key, including a key the file did not hold."""
    doc = tomllib.loads(lines.text_of(change.path))
    table = doc.get(change.table, {})
    return replace(change, given=table.get(change.key))


def confirmed(environ: Mapping[str, str], folder: Path) -> Shown:
    """Require the door's address in the server's reply."""
    shown = ensure.ensure(environ, folder)
    if shown.tailnet is None:
        raise Refusal(
            "door-not-open",
            shown.said or "the board server has no tailnet door for the owner",
            "the owner runs lem serve ensure without LEM_SERVE=off before another attempt",
        )
    return shown
