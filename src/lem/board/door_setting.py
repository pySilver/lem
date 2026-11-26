"""Keep the door's setting only when the server answers with the door open."""

from typing import TYPE_CHECKING

from lem.board import ensure
from lem.kernel import files, locks, paths
from lem.kernel.errors import Refusal
from lem.settings import edit, reading
from lem.settings.write import Asked, checkout_of, edit_for

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from lem.board.facts import Shown


def opened(asked: Asked) -> Shown:
    """Give the child its startup setting and restore the file on failure."""
    where = reading.Where(
        checkout=checkout_of(asked.folder, asked.scope),
        home=paths.home(asked.environ),
        environ=asked.environ,
    )
    change = edit_for(asked, where)
    with locks.held(change.lock):
        before = snapshot(change.path)
        edit.written(change, where)
        try:
            return confirmed(asked.environ, asked.folder)
        except BaseException:
            if before is None:
                change.path.unlink(missing_ok=True)
            else:
                files.write_whole(change.path, before)
            raise


def snapshot(path: Path) -> bytes | None:
    """The exact settings file, or None when there was no file."""
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None


def confirmed(environ: Mapping[str, str], folder: Path) -> Shown:
    """Require the door's address in the server's reply."""
    shown = ensure.ensure(environ, folder)
    if shown.tailnet is None:
        raise Refusal(
            "door-not-open",
            shown.said or "the board server has no tailnet door for the owner",
            "the owner checks lem serve ensure before another attempt",
        )
    return shown
