"""What `tailscale serve status --json` says of this Mac's ports on the tailnet."""

import msgspec

from lem.board.tailscale import STILL_LOCAL, asked
from lem.kernel.errors import Refusal

# What a port proxies to when it is not one address.
OTHER = "another target"


class Path(msgspec.Struct, frozen=True, kw_only=True):
    """One path of a served site: the address it proxies to."""

    proxy: str | None = msgspec.field(default=None, name="Proxy")


class Site(msgspec.Struct, frozen=True, kw_only=True):
    """A served site, by its paths."""

    paths: dict[str, Path] = msgspec.field(default_factory=dict, name="Handlers")


class Served(msgspec.Struct, frozen=True, kw_only=True):
    """What `tailscale serve status --json` says of this Mac's ports."""

    tcp: dict[str, object] = msgspec.field(default_factory=dict, name="TCP")
    web: dict[str, Site] = msgspec.field(default_factory=dict, name="Web")
    funnel: dict[str, bool] = msgspec.field(default_factory=dict, name="AllowFunnel")


def status(cli: str) -> Served:
    """`tailscale serve status --json`."""
    try:
        return msgspec.json.decode(
            asked(cli, ("serve", "status", "--json")), type=Served
        )
    except msgspec.DecodeError as error:
        raise Refusal(
            "tailscale",
            f"tailscale serve status printed no status ({error})",
            STILL_LOCAL,
        ) from error


def proxied_of(site: Site) -> str:
    """The one address the site's `/` proxies to, else OTHER."""
    if set(site.paths) != {"/"}:
        return OTHER
    return (site.paths["/"].proxy or "").rstrip("/") or OTHER
