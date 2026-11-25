"""The port of this machine's board server, and the two ports a test may never take.

The port is `serve.port` of `[serve]` in `machine.toml`, Lem's home folder, else PORT. The
owner's own server listens on PORT and on its door's DOOR_PORT, so a server of any other home
folder (a test's, a trial's) is refused both: nothing it runs may answer there in the owner's
place, nor stop his server to take its port. The first part of every address of the board is
the machine's name, its short host name as a workspace's name is written.
"""

import os
import pwd
import socket
import tomllib
from typing import TYPE_CHECKING, Annotated

import msgspec

from lem.board import workspaces
from lem.kernel import paths
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

# A port that no common tool takes by default (a pick of the proof of concept, not a
# measurement), and the door's beside it.
PORT = 4536
DOOR_PORT = 4537
MACHINE = "machine.toml"

# The highest number a port may have.
HIGHEST_PORT = 65535

type Port = Annotated[int, msgspec.Meta(ge=1, le=HIGHEST_PORT)]


class Serve(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """`[serve]` of the machine's file: the main port, and the door, which this build does
    not open yet."""

    port: Port = PORT
    tailscale: bool = False
    tailscale_port: Port = DOOR_PORT


def settings(home: Path) -> Serve:
    """`[serve]` of `machine.toml` in Lem's home folder `home`; none there is the defaults."""
    path = home / MACHINE
    try:
        tables = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return Serve()
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise Refusal(
            "machine-settings",
            f"{path} does not read: {error}",
            f"write it again as TOML, or remove it for the defaults ({path})",
        ) from error
    try:
        return msgspec.convert(tables.get("serve", {}), Serve)
    except msgspec.ValidationError as error:
        raise Refusal(
            "machine-settings",
            f"[serve] of {path} is not valid: {error}",
            "give port and tailscale_port a number from 1 to 65535, and nothing else",
        ) from error


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
    """This machine's name in the board's addresses: its short host name, as a word."""
    return workspaces.word(socket.gethostname().split(".")[0]) or "this-mac"
