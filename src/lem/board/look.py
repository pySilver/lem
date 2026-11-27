"""The look `lem` takes before a command: it starts the board server, detached and silently, when
`serve.json` in Lem's home folder names no process that lives (`__main__.look_for_server` on
`main`).

`help` and `version` answer before it, and `serve`, `board`, `doctor`, `ask`, `jev` and `uninstall`
take no look: they ask the server their own way, or need none. `LEM_SERVE=off` stops it.
The start is `lem serve ensure` of this install, with its output in `serve.log`, so that the
replace rule decides; every failure is silent, since no command waits for the board or fails by it.
"""

import contextlib
import os
import subprocess
import sys
from typing import TYPE_CHECKING

import msgspec

from lem.kernel import folders, paths
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

NO_LOOK = (
    "serve",
    "board",
    "doctor",
    "ask",
    "jev",
    "uninstall",
    "help",
    "--help",
    "-h",
    "version",
)
SERVE = "serve.json"
LOG = "serve.log"


class Named(msgspec.Struct, frozen=True):
    """The pid `serve.json` names."""

    pid: int


def lives(home: Path) -> bool:
    """Whether `serve.json` names a process that lives; a file that does not read is none."""
    try:
        pid = msgspec.json.decode((home / SERVE).read_bytes(), type=Named).pid
    except OSError, msgspec.DecodeError:
        return False
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def command() -> list[str]:
    """`lem serve ensure` of this interpreter and install."""
    return [sys.executable, "-B", "-P", "-s", "-m", "lem", "serve", "ensure"]


def wanted(first: str | None, environ: Mapping[str, str]) -> bool:
    """Whether the command of the first word `first` takes the look."""
    return environ.get("LEM_SERVE") != "off" and first not in NO_LOOK


def looked(first: str | None, environ: Mapping[str, str]) -> None:
    """Start the server detached when the command takes the look and none lives."""
    if not wanted(first, environ):
        return
    with contextlib.suppress(Refusal, OSError):
        home = paths.home(environ)
        if lives(home):
            return
        folders.home_marked(home)
        started(home, environ)


def started(home: Path, environ: Mapping[str, str]) -> None:
    """Start `lem serve ensure` of this install in a session of its own."""
    package = str(paths.PACKAGE.parent)
    with (home / LOG).open("ab") as log:
        subprocess.Popen(
            command(),
            cwd=home,
            env={**environ, "PYTHONPATH": package},
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
