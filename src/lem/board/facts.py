"""What the board server says of itself, and what the commands of `lem serve` print.

`Facts` is the server's answer to `GET /api/server`, which `serve.json` in Lem's home folder
holds too while it runs: its process, its port, the machine's name in its addresses, the install
it runs, and Lem's home folder it serves. `lem serve ensure` reads it to decide whether the server
that runs stays (the design's part 5, "The server's replace rule").
"""

import msgspec

from lem.records.base import Moment

# The header of the server's own answer and its one value, which no other program on the
# port sends.
HEADER = "Lem-Server"
MARK = "lem"


class Install(msgspec.Struct, frozen=True, kw_only=True):
    """Which install of Lem a process runs: the release its manifest names, the commit a
    build wrote into the package (`build-commit`), the real path of its package, and, with no
    commit, the newest change time of its modules, which an edit of a checkout moves."""

    version: str
    commit: str | None = None
    package: str
    stamp: int | None = None


class Facts(msgspec.Struct, frozen=True, kw_only=True):
    """Who serves: the process, its port and address, the machine's name in its addresses and
    its other name, the install, Lem's home folder, the door's port and its address on the
    tailnet (none while the door is closed), and since when."""

    pid: int
    port: int
    url: str
    host: str
    aliases: tuple[str, ...] = ()
    install: Install
    home: str
    door: int | None = None
    tailnet: str | None = None
    started: Moment


class Shown(msgspec.Struct, frozen=True, kw_only=True, omit_defaults=True):
    """What `lem serve ensure` prints: whether a server runs, whether this call started it,
    who it is, a line when it did not do what was asked, and whether the server is of another
    install that this call leaves as it is."""

    running: bool
    started: bool
    pid: int | None = None
    url: str | None = None
    host: str | None = None
    install: Install | None = None
    said: str | None = None
    another_install: bool = False


class Stopped(msgspec.Struct, frozen=True, kw_only=True, omit_defaults=True):
    """What `lem serve stop` prints: whether a server ended, which, or why none did."""

    stopped: bool
    pid: int | None = None
    version: str | None = None
    said: str | None = None


class Served(msgspec.Struct, frozen=True, kw_only=True):
    """What `lem serve run` prints when its server ended: the process and its port."""

    pid: int
    port: int
    url: str
