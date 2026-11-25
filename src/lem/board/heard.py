"""What an answer of a port to `GET /api/server` says: a board server of this build and this home
folder, a board server of the release before it in this home folder, or something to refuse.

A server of this build marks its answer with `Lem-Server: lem` and names the port it serves and
its home folder. The release before it answers with `Server: lem-serve ...` and names its home
folder `config` (`serve.py` `Handler.server_version` and `RUNNING` on `main`). A command of this
build never stops a server of that form: it says which install serves and changes nothing, and
the cutover's wipe stops it (the design's part 10).
"""

from http import HTTPStatus
from typing import TYPE_CHECKING

import msgspec

from lem.board.facts import MARK, Facts, Install
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from pathlib import Path

    from lem.board.client import Reply

# The first word of the `Server` header of the release before this one.
BEFORE = "lem-serve"


class Other(msgspec.Struct, frozen=True, kw_only=True):
    """A board server of another install, of the release before this one, in this home
    folder: its process, its address and its install."""

    pid: int
    url: str | None = None
    install: Install
    config: str


def held_by_another(port: int, why: str) -> Refusal:
    """The refusal of a port that something else holds."""
    return Refusal(
        "port-held",
        f"port {port} on 127.0.0.1 {why}",
        f"end it (lsof -nP -iTCP:{port} -sTCP:LISTEN names it), or name another port",
    )


def elsewhere(port: int, pid: int, home: str) -> Refusal:
    """The refusal of a port that the board server of another home folder holds."""
    return Refusal(
        "other-home",
        f"port {port} is held by the board server (pid {pid}) of another home folder of "
        f"Lem, {home}",
        "name another port for this home folder",
    )


def decoded[Form](reply: Reply, port: int, form: type[Form]) -> Form:
    """The answer's body in `form`; refused when it is not."""
    try:
        return msgspec.json.decode(reply.body, type=form)
    except msgspec.DecodeError as error:
        raise held_by_another(port, f"answers as no board server ({error})") from error


def found(reply: Reply, port: int) -> Facts | Other:
    """Who answered, of whatever home folder; anything but a board server is refused."""
    if reply.status != HTTPStatus.OK:
        raise held_by_another(port, f"answered /api/server with {reply.status}")
    if reply.server.startswith(BEFORE):
        return decoded(reply, port, Other)
    if reply.marker != MARK:
        raise held_by_another(
            port, "is held by a program that is no board server of Lem"
        )
    facts = decoded(reply, port, Facts)
    if facts.port != port:
        raise held_by_another(port, f"answers for port {facts.port}")
    return facts


def judged(reply: Reply, *, port: int, home: Path) -> Facts | Other:
    """Who answered: this build's server of this home folder, or the release before it in
    this home folder; anything else is refused."""
    who = found(reply, port)
    named = who.config if isinstance(who, Other) else who.home
    if named != str(home):
        raise elsewhere(port, who.pid, named)
    return who


def which(other: Other) -> str:
    """The line that says which install serves, which this command leaves as it is."""
    version = other.install.version
    package = other.install.package
    return (
        f"another install of Lem serves this home folder: release {version} from "
        f"{package} (pid {other.pid}); this one changes nothing"
    )
