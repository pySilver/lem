"""`lem.log`: where a fault's traceback goes, so that the owner reads one line and the
maintainer finds the rest.

Each entry is the moment, the command line, and the traceback, appended under the log's own
lock; the envelope's `fault` names the line and this file. A command imports this module only
on a fault (`cli/faults.py`), and it imports no `logging`, which cost about 5 ms a call
(unmeasured estimate of the step `tree`, notes/tree.md). A log that cannot be written gets the
traceback on standard error, and the envelope says why.
"""

import shlex
import sys
import traceback
from typing import TYPE_CHECKING

from lem.kernel import clock, folders, locks
from lem.kernel.envelope import Failed
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

LOG = "lem.log"


def entry(error: BaseException, argv: list[str]) -> str:
    """The text one fault adds to the log: its moment and command line, then its traceback."""
    moment = clock.now().isoformat()
    command = shlex.join(argv)
    told = "".join(traceback.format_exception(error))
    return f"{moment} lem {command}\n{told}\n"


def first_line(error: BaseException) -> str:
    """What the owner reads of a fault: its first line, else its kind."""
    said = str(error).strip().splitlines()
    return said[0] if said else type(error).__name__


def fault(log: Path, error: BaseException, argv: list[str]) -> Failed:
    """Append the traceback of `error` to `log`, and give the envelope's fault: the error's
    first line for the owner, and where its traceback is."""
    log.parent.mkdir(parents=True, exist_ok=True)
    lock = log.with_name(f"{log.name}.lock")
    with locks.held(lock), log.open("a", encoding="utf-8") as stream:
        stream.write(entry(error, argv))
    return Failed(line=first_line(error), log=str(log))


def logged(error: BaseException, argv: list[str], environ: Mapping[str, str]) -> Failed:
    """The fault of a command: its traceback in `lem.log` of Lem's home folder, else on
    standard error with the reason the log could not be written."""
    try:
        return fault(folders.home_for_writing(environ) / LOG, error, argv)
    except (OSError, Refusal) as unwritten:
        sys.stderr.write(entry(error, argv))
        line = first_line(error)
        return Failed(
            line=line, log=f"standard error: the log could not be written ({unwritten})"
        )
