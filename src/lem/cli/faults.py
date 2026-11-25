"""Where a fault of Lem goes: its traceback to `lem.log` in Lem's home folder, a line to the owner.

`lazy.main` loads this module only on a fault, so a call that succeeds pays nothing for it. A
local seam until `kernel/` has the log of every part of Lem
(`docs/plans/2026-11-25-lem-built-again/notes/tree.md`).
"""

import os
import sys
import traceback
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lem.kernel.errors import Fault


def home() -> Path:
    """Lem's home folder: `$XDG_CONFIG_HOME/lem`, else `~/.config/lem`; a relative
    `XDG_CONFIG_HOME` names no home, and the log goes to standard error."""
    named = os.environ.get("XDG_CONFIG_HOME", "")
    if named and not Path(named).is_absolute():
        raise OSError(f"XDG_CONFIG_HOME={named} is no absolute folder")
    config = Path(named) if named else Path.home() / ".config"
    return config / "lem"


def logged(fault: Fault) -> tuple[str, str]:
    """Append the fault's traceback to `lem.log`; give its line and where the traceback went.

    A log that cannot be written gets the traceback on standard error, and the place says why.
    """
    moment = datetime.now(UTC).isoformat(timespec="seconds")
    record = "".join((f"{moment} a fault of Lem\n", *traceback.format_exception(fault)))
    try:
        where = appended(record)
    except OSError as why:
        sys.stderr.write(record)
        return str(fault), f"standard error: {why}"
    return str(fault), where


def appended(record: str) -> str:
    """Append `record` to `lem.log` in Lem's home folder, made when it is not there; give the
    file's path."""
    path = home() / "lem.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as log:
        log.write(record)
    return str(path)
