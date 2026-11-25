"""The rows of the board server: whether one runs and which install it runs, the door for the
owner's phone, and the board's notifications.

The check reads only the files the server keeps in Lem's home folder (`serve.json`, written at
its start and removed at its clean stop) and asks the process table whether the pid there still
runs. It never connects to the server and never starts one.
"""

import os
import shlex
from typing import TYPE_CHECKING

import msgspec

from lem.board import install
from lem.board.facts import Facts
from lem.board.serve_file import SERVE
from lem.cli.doctor.picker import stable_lem
from lem.cli.doctor.row import OPTIONAL, Row
from lem.kernel import paths
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from lem.cli.doctor.look import Look

SERVER_USED_FOR = (
    "the boards of every repository on this machine in a browser of another device, the "
    "owner's phone through his tailnet (`lem serve door on`, one time); the first Claude "
    "Code session in a repository that uses Lem starts it"
)


def running(look: Look) -> Facts | None:
    """The facts of the server that runs, from `serve.json`; None when the file is not there
    or names a process that no longer runs. A file that does not read is refused, and the
    row says why."""
    path = paths.home(look.environ) / SERVE
    try:
        facts = msgspec.json.decode(path.read_bytes(), type=Facts)
    except FileNotFoundError:
        return None
    except (OSError, msgspec.DecodeError) as error:
        raise Refusal(
            "serve-file",
            f"{path} does not read: {error}",
            f"lem serve stop, or remove {path} when no server runs",
        ) from error
    return facts if alive(facts.pid) else None


def alive(pid: int) -> bool:
    """Whether the process `pid` runs: a signal 0 is sent to nobody."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def ensure_line(look: Look) -> str:
    """The line that starts the server from a terminal with no agent: the app's command by its
    path that an update keeps, whatever the PATH holds."""
    command = stable_lem(look)
    if command is None:
        return "lem serve ensure"
    quoted = shlex.quote(str(command))
    return f"{quoted} serve ensure"


def whose(facts: Facts) -> str:
    """Which install serves, against this one: the same, older, or another that stays."""
    mine = install.install_of()
    theirs = facts.install
    said = f"it runs Lem {theirs.version} from {theirs.package}"
    if install.replaces(mine, theirs, settings_differ=False):
        return f"{said}, and this Lem is {mine.version}: the next `lem serve ensure` replaces it"
    if mine == theirs:
        return f"{said}, this install"
    return f"{said}; this Lem is {mine.version} from {mine.package}, and leaves it as it is"


def server_row(look: Look) -> Row:
    """The board server of this machine: whether one runs, where, and which install. Optional:
    the board opens in agterm without it."""
    line = ensure_line(look)
    facts = running(look)
    if facts is None:
        path = paths.home(look.environ) / SERVE
        return Row(
            name="board server",
            need=OPTIONAL,
            found=False,
            detail=f"no server runs: {path} names none",
            used_for=SERVER_USED_FOR,
            without_it=(
                "the board opens in agterm only, until a Claude Code session starts in a "
                "repository that uses Lem; after a remote login with no agent, "
                f"`{line}` in the terminal"
            ),
            line=line,
        )
    serving = whose(facts)
    return Row(
        name="board server",
        need=OPTIONAL,
        found=True,
        detail=f"pid {facts.pid} serves {facts.url}; {serving}",
        used_for=SERVER_USED_FOR,
        without_it=None,
        line=line,
    )
