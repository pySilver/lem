"""The tailnet door: the second listener, on 127.0.0.1 behind `tailscale serve`, which the owner's
phone reaches as `https://MAC.TAILNET.ts.net:PORT/`, and its check of every request
(`serve.door_refusal` on `main`).

Tailscale puts the login of the person who asks into `Tailscale-User-Login`; the door lets in
only the owner's own login, the one this Mac is signed in with, never a request that came
through Funnel, and only for the Mac's own name on the tailnet in `Host`. A method other than
GET and HEAD must also come from the board's own page: a `Sec-Fetch-Site` that is not
same-origin and an `Origin` that is not the board's are refused. A login that is not the
owner's makes the door read his login again, at most once in RECHECK seconds, since a Mac's
account can change while the server runs.
"""

import threading
import time
from dataclasses import dataclass, field
from email.header import decode_header, make_header
from http.client import HTTPS_PORT
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

type Seen = dict[str, list[str]]

# How often, at most, a login that is not the owner's makes the door read his login again. A
# guess: often enough to follow a change of account, rare enough that a peer of the tailnet
# cannot make the Mac run the CLI at will (`serve.LOGIN_RECHECK_SECONDS` on `main`).
RECHECK = 30.0
NOT_THE_OWNER = (
    "Only the owner's own Tailscale login opens this board, "
    "and this request carries another login."
)
READS = frozenset(("GET", "HEAD"))
SAME_SITE = frozenset(("same-origin", "none"))


def seen_of(headers: Iterable[tuple[str, str]]) -> Seen:
    """Each header's values by its name in lower case, each value as often as it came."""
    seen: Seen = {}
    for name, word in headers:
        seen.setdefault(name.lower(), []).append(word.strip())
    return seen


def decoded(word: str) -> str:
    """A header's value with its RFC 2047 words decoded, which Tailscale uses for a login that
    is not plain ASCII; the value as it came when it does not decode."""
    try:
        return str(make_header(decode_header(word)))
    except ValueError, LookupError:
        return word


def login_refusal(seen: Seen, owner: str) -> str | None:
    """None when the request carries one login, the owner's."""
    logins = seen.get("tailscale-user-login", [])
    if not logins:
        return (
            "Only the owner's own Tailscale login opens this board, "
            "and this request carries none."
        )
    named = decoded(logins[0]).casefold()
    if len(logins) > 1 or named != owner.strip().casefold():
        return NOT_THE_OWNER
    return None


def origins(served: str, port: int) -> frozenset[str]:
    """The board's own origins at the door."""
    name = served.lower()
    with_port = f"https://{name}:{port}"
    if port == HTTPS_PORT:
        return frozenset((with_port, f"https://{name}"))
    return frozenset((with_port,))


def change_refusal(seen: Seen, served: str, port: int) -> str | None:
    """None when a change comes from the board's own page."""
    fetch = {word.lower() for word in seen.get("sec-fetch-site", [])}
    if not fetch <= SAME_SITE:
        return (
            "A change comes only from the board's own page, "
            "and this request comes from another site."
        )
    named = {word.lower() for word in seen.get("origin", [])}
    if not named <= origins(served, port):
        return (
            "A change comes only from the board's own page, "
            "and this request names another origin."
        )
    return None


def door_refusal(
    seen: Seen, method: str, owner: str, served: str, port: int
) -> str | None:
    """None when the door lets the request in, else the line its 403 says: `owner` is the
    owner's login, `served` the Mac's name on the tailnet, `port` the door's HTTPS port."""
    if "tailscale-funnel-request" in seen:
        return "This board is not served through Tailscale Funnel."
    hosts = [word.lower() for word in seen.get("host", [])]
    own = {served.lower(), f"{served.lower()}:{port}"}
    if len(hosts) != 1 or hosts[0] not in own:
        return "This address is not the board's name on the tailnet."
    refused = login_refusal(seen, owner)
    if refused is None and method.upper() not in READS:
        return change_refusal(seen, served, port)
    return refused


@dataclass
class Door:
    """What the door checks a request against: the Mac's name on the tailnet, the door's
    port, the owner's login, and the look that reads his login again, which gives the one
    before when it cannot."""

    name: str
    port: int
    owner: str
    reread: Callable[[str], str]
    read_at: float = field(default_factory=time.monotonic)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def url(self) -> str:
        """The door's address on the tailnet."""
        if self.port == HTTPS_PORT:
            return f"https://{self.name}/"
        return f"https://{self.name}:{self.port}/"

    def refusal(self, seen: Seen, method: str) -> str | None:
        """The door's check, with the owner's login read again when the request's is
        another's and RECHECK passed since the last read."""
        refused = door_refusal(seen, method, self.owner, self.name, self.port)
        if refused == NOT_THE_OWNER and self.fresh_owner():
            return door_refusal(seen, method, self.owner, self.name, self.port)
        return refused

    def fresh_owner(self) -> bool:
        """Read the owner's login again, at most once in RECHECK; True when it changed."""
        with self.lock:
            if time.monotonic() - self.read_at < RECHECK:
                return False
            self.read_at = time.monotonic()
            before = self.owner
            self.owner = self.reread(before)
            return self.owner != before
