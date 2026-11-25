"""`lem.log`: where a fault's traceback goes, so that the owner reads one line and the
maintainer finds the rest.

Each entry is the moment, the command line, and the traceback, appended under the log's own
lock; the envelope's `fault` names the line and this file.
"""

import shlex
import traceback
from typing import TYPE_CHECKING

from lem.kernel import clock, locks
from lem.kernel.envelope import Failed

if TYPE_CHECKING:
    from pathlib import Path


def entry(error: BaseException, argv: list[str]) -> str:
    """The text one fault adds to the log: its moment and command line, then its traceback."""
    moment = clock.now().isoformat()
    command = shlex.join(argv)
    told = "".join(traceback.format_exception(error))
    return f"{moment} lem {command}\n{told}\n"


def fault(log: Path, error: BaseException, argv: list[str]) -> Failed:
    """Append the traceback of `error` to `log`, and give the envelope's fault: the error's
    first line for the owner, and where its traceback is."""
    log.parent.mkdir(parents=True, exist_ok=True)
    lock = log.with_name(f"{log.name}.lock")
    with locks.held(lock), log.open("a", encoding="utf-8") as stream:
        stream.write(entry(error, argv))
    said = str(error).strip().splitlines()
    line = said[0] if said else type(error).__name__
    return Failed(line=line, log=str(log))
