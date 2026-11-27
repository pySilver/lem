"""Files for overlays and the Stop hook's record of the last wait."""

import contextlib
import json
import tempfile
import time
from pathlib import Path
from typing import TYPE_CHECKING

from lem.app.asking import keys
from lem.kernel import files

if TYPE_CHECKING:
    from lem.app.asking.overlay_tree import Overlay

# The lifetime of a generated page, as on main.
PRIVATE_MODE = 0o700
KEEP = 86400
QUIET = ".no-status.html"
ASKING = ("blocked",)


def folder() -> Path:
    """Where the overlay pages of lem ask live."""
    return Path(tempfile.gettempdir()).resolve() / "lem-ask"


def page_file(body: bytes, *, quiet: bool) -> Path:
    """Write the page under a private name that marks the first status choice."""
    home = folder()
    home.mkdir(mode=PRIVATE_MODE, exist_ok=True)
    prune(home)
    suffix = QUIET if quiet else ".html"
    with tempfile.NamedTemporaryFile(dir=home, suffix=suffix, delete=False) as stream:
        stream.write(body)
        return Path(stream.name)


def prune(home: Path) -> None:
    """Remove an expired page or wait word from this command's folder."""
    older = time.time() - KEEP
    for path in home.glob("*.html"):
        with contextlib.suppress(FileNotFoundError):
            if path.stat().st_mtime < older:
                path.unlink(missing_ok=True)


def remember(page: str, asking: tuple[str, ...] | None) -> None:
    """Keep the latest mark for the Stop hook, or the choice to leave it alone."""
    home = folder()
    home.mkdir(mode=PRIVATE_MODE, exist_ok=True)
    named = keys.checked(page)
    files.write_whole(home / f"{named}.wait.html", wait_word(asking))


def wait_word(asking: tuple[str, ...] | None) -> bytes:
    """Keep the plain words for the two default choices."""
    if asking is None:
        return b"no-status"
    return b"status" if asking == ASKING else json.dumps(asking).encode()


def ours(overlays: tuple[Overlay, ...], page: str | None = None) -> str | None:
    """The id of an open question page of ours, or none."""
    return next((overlay.id for overlay in overlays if matches(overlay, page)), None)


def matches(overlay: Overlay, page: str | None) -> bool:
    """Whether the exact page is one lem ask opened in this session."""
    path = overlay.path
    return (
        bool(path)
        and page in (None, overlay.id)
        and Path(path or "").resolve().parent == folder()
    )
