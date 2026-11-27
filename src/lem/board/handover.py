"""The hand-over of a board server whose own install was replaced (`replaced.py`) to the
installed Lem.

Every LOOK seconds the server looks at its install. When an update replaced it, the server's
answer to `GET /api/server` says why, and the server starts `lem serve ensure` of the installed
Lem once for each reason, as the serve hook does, with its output in the server's log. That
`ensure` stops this server, whatever its release, and starts its own: the swap of a newer
install, with the board's update notice when the release is higher. With no installed Lem, or
when that `ensure` leaves this server as it is, the server says why in its log and keeps
serving what it can.
"""

import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from lem.board import install, replaced, start
from lem.board.turns import Turn
from lem.kernel import paths, release

if TYPE_CHECKING:
    from collections.abc import Mapping

# How often the server looks at its install, in seconds. A guess: the watcher's period, so that
# few of its looks fail before the hand-over; each look reads a few files.
LOOK = 5.0
NAME = "the look at its install"
# The folder of the standard library this process imports from, which `os` is a module of.
STDLIB = Path(os.__file__).parent
# The variable `lem serve ensure` sets for the server it starts, which would make the installed
# Lem import the package of this server.
IMPORTS = "PYTHONPATH"


def launched(
    command: Path, home: Path, environ: Mapping[str, str]
) -> subprocess.Popen[bytes]:
    """Start `command serve ensure` in a session of its own, with no input, its output in the
    server's log, and the server's environment without its package on the import path."""
    told = {name: word for name, word in environ.items() if name != IMPORTS}
    with (home / start.LOG).open("ab") as log:
        return subprocess.Popen(
            [str(command), "serve", "ensure"],
            cwd="/",
            env=told,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )


def say(line: str) -> None:
    """One line in the server's log."""
    sys.stderr.write(f"lem serve: {line}\n")


@dataclass(kw_only=True)
class Handover:
    """What the server started from, where it runs, and what it did so far: why its install
    is replaced now, which the server's answer says, the reasons it handed over for, those it
    found no installed Lem for, and the `ensure` it started, while that runs."""

    version: str
    commit: str | None
    package: Path
    stdlib: Path
    executable: Path
    home: Path
    environ: Mapping[str, str]
    why: str | None = None
    handed: set[str] = field(default_factory=set)
    unserved: set[str] = field(default_factory=set)
    child: subprocess.Popen[bytes] | None = None

    def look(self) -> None:
        """One look: the end of the `ensure` it started, else the hand-over its install
        needs."""
        if self.child is not None:
            self.ended(self.child)
            return
        why = replaced.replaced(self.version, self.commit, self.package, self.stdlib)
        self.why = why
        if why is None or why in self.handed:
            return
        command = replaced.successor(self.package, self.executable)
        said = f"Lem's install of this board server was replaced: {why}"
        if command.is_file() and os.access(command, os.X_OK):
            self.handed.add(why)
            say(f"{said}. It hands over to `{command} serve ensure`")
            self.child = launched(command, self.home, self.environ)
        elif why not in self.unserved:
            self.unserved.add(why)
            say(
                f"{said}. No installed Lem is at {command}, so this server keeps serving "
                "what it can: the owner installs Lem again, or runs `lem serve ensure`"
            )

    def ended(self, child: subprocess.Popen[bytes]) -> None:
        """Say once that the `ensure` it started ended and left this server."""
        code = child.poll()
        if code is None:
            return
        self.child = None
        say(
            f"the hand-over ended with status {code}, and this server still serves: "
            "the lines before this one say why"
        )


def watching(home: Path) -> Handover:
    """The hand-over of this process's install, read as the server starts, with the
    server's environment."""
    return Handover(
        version=release.running(),
        commit=install.commit_of(paths.PACKAGE),
        package=paths.PACKAGE,
        stdlib=STDLIB,
        executable=Path(sys.executable),
        home=home,
        environ=os.environ,
    )


def turn(held: Handover) -> Turn:
    """The look as a loop of the server's life: one every LOOK seconds."""
    return Turn(name=NAME, every=LOOK, step=held.look)
