"""What the rows of `lem doctor` look at: the environment, the user's home, the folder of the
call, this app's Python, and the programs on the environment's PATH.

Every row takes one `Look`, so a test gives it a home of its own, a PATH of stand-in scripts and
Homebrew's prefixes in a temporary folder, and never reaches the owner's own files or tools. A
program is run with a timeout and its first line read. The connections a row may make, to
cronn's status on this machine and to the board of each machine joined to this one, go through
`answers` and `board_live`, which a test replaces.
"""

import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from http.client import HTTPConnection, HTTPException
from pathlib import Path
from typing import TYPE_CHECKING

from lem.cli.doctor.peer_look import board_live

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

# How long a program the check runs may take, in seconds (a guess: a `--version` answers at
# once, and a stuck one must not hold the check).
RUN_WAIT = 10
# How long cronn's status may take to answer, in seconds.
STATUS_WAIT = 2
# Homebrew's prefixes, on Apple silicon and on Intel.
BREWS = (Path("/opt/homebrew"), Path("/usr/local"))
LOOPBACK = "127.0.0.1"
STATUS = "/api/v1/status"
OK = 200


def answers(port: int) -> bool:
    """Whether cronn's status on this machine's `port` answers 200."""
    connection = HTTPConnection(LOOPBACK, port, timeout=STATUS_WAIT)
    try:
        status = asked(connection)
    except OSError, HTTPException:
        return False
    finally:
        connection.close()
    return status == OK


def asked(connection: HTTPConnection) -> int:
    """The status of cronn's answer on `connection`."""
    connection.request("GET", STATUS)
    return connection.getresponse().status


@dataclass(frozen=True, kw_only=True)
class Look:
    """The environment, the user's home, the folder of the call, the app's Python and its
    environment's prefix, Homebrew's prefixes, the question to cronn's status, and the question
    to a joined machine's board whether its agterm runs Live sessions."""

    environ: Mapping[str, str]
    home: Path
    folder: Path
    executable: Path = Path(sys.executable)
    prefix: Path = Path(sys.prefix)
    brews: tuple[Path, ...] = BREWS
    status: Callable[[int], bool] = field(default=answers)
    peer_live: Callable[[str, int], tuple[bool | None, str]] = field(default=board_live)

    def which(self, name: str) -> Path | None:
        """The program `name` first on the environment's PATH."""
        found = shutil.which(name, path=self.environ.get("PATH", ""))
        return Path(found) if found else None

    def first_line(self, argv: tuple[str, ...]) -> str | None:
        """The first line a program printed, when it exited 0; None for anything else."""
        ran = self.ran(argv)
        if ran is None or ran.returncode:
            return None
        lines = (ran.stdout or ran.stderr).strip().splitlines()
        return lines[0] if lines else None

    def succeeds(self, argv: tuple[str, ...]) -> bool:
        """Whether a program exited 0."""
        ran = self.ran(argv)
        return ran is not None and not ran.returncode

    def ran(self, argv: tuple[str, ...]) -> subprocess.CompletedProcess[str] | None:
        """A program run to its end with the environment, or None when it did not start or
        took too long."""
        try:
            return subprocess.run(
                argv,
                capture_output=True,
                text=True,
                check=False,
                timeout=RUN_WAIT,
                env=dict(self.environ),
            )
        except OSError, subprocess.TimeoutExpired:
            return None


def looked(environ: Mapping[str, str], folder: Path) -> Look:
    """The look of a call of `lem doctor` from `folder`."""
    home = environ.get("HOME") or str(Path.home())
    return Look(environ=environ, home=Path(home), folder=folder)
