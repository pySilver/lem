"""The port of this machine's board server, and the two ports a test may never take.

The port is `serve.port` of `[serve]` in `machine.toml`, Lem's home folder, else PORT (the
machine's settings, `lem.settings.load.machine_of`). The
owner's own server listens on PORT and on its door's DOOR_PORT, so a server of any other home
folder (a test's, a trial's) is refused both: nothing it runs may answer there in the owner's
place, nor stop his server to take its port. The first part of every address of the board is
the machine's name: its first label on the tailnet when Tailscale runs, else its short host
name, as a workspace's name is written.
"""

import os
import pwd
import socket
from typing import TYPE_CHECKING

from lem.board import workspaces
from lem.kernel import paths
from lem.kernel.errors import Refusal
from lem.settings.load import machine_of
from lem.settings.machine import DOOR_PORT, PORT, Serve

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

MACHINE = "machine.toml"


def settings(home: Path) -> Serve:
    """`[serve]` of `machine.toml` in Lem's home folder `home`, as the settings read and check
    it; none there is the defaults."""
    return machine_of(home, os.environ).serve


def owners_home(environ: Mapping[str, str]) -> bool:
    """Whether Lem's home folder of `environ` is the one of the user's real home, as the
    password database names it, and no throwaway one."""
    real = pwd.getpwuid(os.getuid()).pw_dir
    return paths.home(environ) == paths.home({"HOME": real})


def allowed(port: int, environ: Mapping[str, str]) -> bool:
    """Whether a command of the home folder of `environ` may contact or serve `port`: not
    one of the owner's two, unless the home folder is his."""
    return port not in {PORT, DOOR_PORT} or owners_home(environ)


def guarded(port: int, environ: Mapping[str, str]) -> int:
    """`port`, unless it is one of the owner's two and the home folder is not his."""
    if not allowed(port, environ):
        raise Refusal(
            "owner-port",
            f"port {port} is the owner's own board server's, and {paths.home(environ)} "
            "is not his home folder of Lem: a server of another home never takes it",
            f"name another port: lem serve run --port N, or [serve] port in {MACHINE}",
        )
    return port


def port_of(home: Path, environ: Mapping[str, str], given: int | None = None) -> int:
    """The port a call serves: the one it names, else the machine's setting; refused when it
    is the owner's and the home folder is not."""
    chosen = settings(home).port if given is None else given
    return guarded(chosen, environ)


def machine_name() -> str:
    """This machine's short host name, as a word of an address."""
    return workspaces.word(socket.gethostname().split(".")[0]) or "this-mac"


def names_of(tailnet_name: str | None) -> tuple[str, tuple[str, ...]]:
    """The machine's name in every address of the board and its other name, which goes to
    the same page: the first label of its name on the tailnet, with the short host name as the
    other when the two differ; else the short host name alone (`serve.names_of` on `main`)."""
    short = machine_name()
    first = workspaces.word((tailnet_name or "").split(".")[0])
    if not first:
        return short, ()
    return first, () if first == short else (short,)
