"""Where a fault of Lem goes: its traceback to `lem.log` in Lem's home folder, a line to the owner.

A local seam until `kernel/` has the log of every part of Lem
(`docs/plans/2026-11-25-lem-built-again/notes/tree.md`).
"""

import logging
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator

# The logger a fault is written with, which `logged` points at `lem.log`.
LOGGER = "lem"


def home() -> Path:
    """Lem's home folder: `$XDG_CONFIG_HOME/lem`, else `~/.config/lem`."""
    named = os.environ.get("XDG_CONFIG_HOME", "")
    config = Path(named) if named else Path.home() / ".config"
    return config / "lem"


@contextmanager
def logged() -> Generator[str]:
    """Send the logger LOGGER to `lem.log` while the block runs, and give where it went.

    A log that cannot be written sends the record to standard error, and the place says why.
    """
    path = home() / "lem.log"
    try:
        sink = opened(path)
    except OSError as why:
        sink = logging.StreamHandler(sys.stderr)
        where = f"standard error: {path} could not be written ({why})"
    else:
        where = str(path)
    sink.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    log = logging.getLogger(LOGGER)
    log.propagate = False
    log.addHandler(sink)
    try:
        yield where
    finally:
        log.removeHandler(sink)
        sink.close()


def opened(path: Path) -> logging.Handler:
    """A handler that appends to the file at `path`, its folder made when it is not there."""
    path.parent.mkdir(parents=True, exist_ok=True)
    return logging.FileHandler(path, encoding="utf-8")


def line(error: BaseException) -> str:
    """The fault in one line for the owner."""
    kind = type(error).__name__
    said = " ".join(str(error).split())
    return f"Lem failed: {kind}: {said}"
