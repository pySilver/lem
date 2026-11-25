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


class Unrelated(Refusal):
    """A reply that does not come from a board server for this home folder."""


def held(port: int, why: str, *, unrelated: bool = False) -> Refusal:
    """The refusal of an occupied port, with the reply's identity when it is known."""
    kind = Unrelated if unrelated else Refusal
    return kind(
        "port-held",
        f"port {port} {why}",
        f"end it (lsof -nP -iTCP:{port} -sTCP:LISTEN names it), or name another port",
    )


def decoded[Form](reply: Reply, port: int, form: type[Form]) -> Form:
    """The answer's body in `form`; refused when it is not."""
    try:
        return msgspec.json.decode(reply.body, type=form)
    except msgspec.DecodeError as error:
        raise held(port, f"answers as no board server ({error})") from error


def found(reply: Reply, port: int) -> Facts | Other:
    """Who answered, of whatever home folder; anything but a board server is refused."""
    before = reply.server.startswith(BEFORE)
    marked = reply.marker == MARK
    if reply.status != HTTPStatus.OK:
        why = f"answered /api/server with {reply.status}"
        raise held(port, why, unrelated=not (before or marked))
    if before:
        return decoded(reply, port, Other)
    if not marked:
        raise held(
            port, "is held by a program that is no board server of Lem", unrelated=True
        )
    facts = decoded(reply, port, Facts)
    if facts.port != port:
        raise held(port, f"answers for port {facts.port}")
    return facts


def judged(reply: Reply, *, port: int, home: Path) -> Facts | Other:
    """Who answered: this build's server of this home folder, or the release before it in
    this home folder; anything else is refused."""
    who = found(reply, port)
    named = who.config if isinstance(who, Other) else who.home
    if named != str(home):
        raise Unrelated(
            "other-home",
            f"port {port} is held by the board server (pid {who.pid}) of another home folder of "
            f"Lem, {named}",
            "name another port for this home folder",
        )
    return who


def which(other: Other) -> str:
    """The line that says which install serves, which this command leaves as it is."""
    version = other.install.version
    package = other.install.package
    return (
        f"another install of Lem serves this home folder: release {version} from "
        f"{package} (pid {other.pid}); this one changes nothing"
    )
