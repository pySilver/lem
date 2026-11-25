"""This Mac on the tailnet, as `tailscale status --json` says: its name there and the
owner's login, which the door lets in alone (`serve.tailnet` on `main`).
"""

from typing import TYPE_CHECKING

import msgspec

from lem.board.tailscale import STILL_LOCAL, WAIT, asked, cli
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from collections.abc import Mapping

# How long the look at the name at a server's start may take. A guess.
NAME_WAIT = 3.0


class Me(msgspec.Struct, frozen=True, kw_only=True):
    """This Mac's part of `tailscale status --json`."""

    name: str = msgspec.field(default="", name="DNSName")
    user: int | None = msgspec.field(default=None, name="UserID")
    tags: tuple[str, ...] | None = msgspec.field(default=None, name="Tags")


class User(msgspec.Struct, frozen=True, kw_only=True):
    """A user of `tailscale status --json`."""

    login: str = msgspec.field(default="", name="LoginName")


class Status(msgspec.Struct, frozen=True, kw_only=True):
    """What the door reads of `tailscale status --json`."""

    state: str = msgspec.field(default="", name="BackendState")
    me: Me = msgspec.field(default_factory=Me, name="Self")
    users: dict[str, User] = msgspec.field(default_factory=dict, name="User")
    certs: tuple[str, ...] | None = msgspec.field(default=None, name="CertDomains")


def status(path: str, wait: float = WAIT) -> Status:
    """`tailscale status --json`, as the door reads it."""
    printed = asked(path, ("status", "--json"), wait)
    try:
        return msgspec.json.decode(printed, type=Status)
    except msgspec.DecodeError as error:
        raise Refusal(
            "tailscale", f"tailscale status printed no status ({error})", STILL_LOCAL
        ) from error


def facts(found: Status) -> tuple[str, str]:
    """This Mac's name on the tailnet and the owner's login, with what the door needs: a
    connected Tailscale, a Mac a person owns (no tag), and HTTPS certificates."""
    user = found.users.get(str(found.me.user), User())
    name = found.me.name.rstrip(".")
    lacks = (
        (found.state != "Running", f"Tailscale is not connected ({found.state})"),
        (bool(found.me.tags), "this Mac is a tagged node, and a tag sends no login"),
        (not found.certs, "HTTPS certificates are off for this tailnet"),
        (not name or not user.login, "tailscale status names no name or no login"),
    )
    for lack, why in lacks:
        if lack:
            raise refused(why)
    return name, user.login


def refused(why: str) -> Refusal:
    """The refusal of a door that cannot open, and why."""
    return Refusal(
        "tailnet",
        f"the door cannot open: {why}",
        "the owner connects Tailscale with his own account and turns on MagicDNS "
        f"and HTTPS (https://tailscale.com/kb/1153/enabling-https); {STILL_LOCAL}",
    )


def name_of(environ: Mapping[str, str]) -> str | None:
    """This Mac's name on the tailnet, asked once within NAME_WAIT; None where no CLI is, or
    Tailscale does not run."""
    path = cli(environ)
    if path is None:
        return None
    try:
        found = status(path, NAME_WAIT)
    except Refusal:
        return None
    return found.me.name.rstrip(".") if found.state == "Running" else None
