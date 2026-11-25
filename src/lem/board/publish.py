"""The door's entry in `tailscale serve`: the tailnet's HTTPS port in front of the door's
listener on 127.0.0.1, put there at a start with the door on and taken out when the owner closes
the door or moves it (`serve.publish` and `serve.tailscale_off` on `main`).

Before it publishes, it reads `tailscale serve status --json`: a port that another target holds
is refused, never taken over, and an entry that points at the door already is kept. Funnel is
never used, and a port Funnel serves is refused. The entry stays when the server stops, and
Tailscale keeps it across a restart of the Mac; the removal takes out only an entry that points
at Lem's door.
"""

from typing import Literal

from lem.board.served import Site, proxied_of, status
from lem.board.tailscale import STILL_LOCAL, asked, door_address
from lem.kernel.errors import Refusal

type Published = Literal["kept", "published"]

CODE = "door-port"


def target(cli: str, name: str, port: int) -> tuple[bool, str, bool]:
    """The tailnet's port `port`: whether an entry holds it, the one address its `/` proxies
    to (OTHER when it serves anything else), and whether Funnel is on for it."""
    found = status(cli)
    key = f"{name}:{port}"
    site = found.web.get(key, Site())
    held = str(port) in found.tcp or bool(site.paths)
    return held, proxied_of(site), found.funnel.get(key, False)


def publish(cli: str, name: str, port: int) -> Published:
    """Put the tailnet's HTTPS port `port` in front of the door: `kept` when it is there,
    `published` when this call put it there. A port another target holds is refused."""
    door = door_address(port)
    held, proxied, funnel = target(cli, name, port)
    if funnel:
        raise Refusal(
            CODE,
            f"Tailscale Funnel is on for port {port}, which would put the board on the internet",
            f"tailscale funnel --https={port} off, or another port: "
            "lem settings set serve.tailscale_port N --machine",
        )
    if held and proxied != door:
        raise Refusal(
            CODE,
            f"port {port} of this Mac on the tailnet serves {proxied}, "
            "and Lem never takes a port of another entry",
            "name a free one: lem settings set serve.tailscale_port N --machine",
        )
    if held:
        return "kept"
    asked(cli, ("serve", "--bg", f"--https={port}", door))
    if target(cli, name, port)[1] != door:
        raise Refusal(
            CODE,
            f"tailscale serve --bg --https={port} {door} did not put the door on the tailnet",
            f"read tailscale serve status; {STILL_LOCAL}",
        )
    return "published"


def removed(cli: str, name: str, port: int) -> bool:
    """Take Lem's entry of the port out of `tailscale serve`: False when the port serves
    nothing; refused when it serves another target than Lem's door."""
    door = door_address(port)
    held, proxied, _ = target(cli, name, port)
    if not held:
        return False
    if proxied != door:
        raise Refusal(
            CODE,
            f"port {port} of this Mac on the tailnet serves {proxied}, "
            f"not Lem's door ({door}): Lem leaves another entry as it is",
            "name Lem's port: lem settings set serve.tailscale_port N --machine",
        )
    asked(cli, ("serve", f"--https={port}", "off"))
    if target(cli, name, port)[0]:
        raise Refusal(
            CODE,
            f"tailscale serve --https={port} off did not take the entry out",
            f"run tailscale serve --https={port} off by hand",
        )
    return True
