"""Who asks for an act of the board: the listener it came to, the device, and the browser's own
words; and the main listener's check that only the board's own page on this Mac acts
(`serve.action_refusal` and `device_of` on `main`).

On the main listener an act comes from the loopback address, with one `Origin`, the board's own,
and no `Sec-Fetch-Site` but `same-origin`; the `Host` was checked before any route
(`board/shield.py`). A form of another site, or one sent with the `Origin` `null`, acts on
nothing. Through the tailnet door the door's own check (his login, the same origin) ran before
the route, on the door's app, whose state says `door`.
"""

import re
from typing import TYPE_CHECKING, Literal

from lem.board.shield import LOOPBACK_NAMES
from lem.records.base import Frozen

if TYPE_CHECKING:
    from starlette.datastructures import Headers
    from starlette.requests import Request

type Via = Literal["local", "door"]
type Device = Literal["phone", "computer"]

# The addresses of a page on this Mac.
LOOPBACK = ("127.0.0.1", "::1")
# A request that names a phone: the client hint of a mobile browser, or a User-Agent that names
# an iPhone, an iPad or Android. A phone in a desktop mode says it is a computer, and the record
# keeps the User-Agent whole beside it.
PHONE = re.compile(r"\b(iPhone|iPad|Android)\b")
SAME_ORIGIN = "same-origin"


class Asker(Frozen, frozen=True, kw_only=True):
    """Where an act came from: the listener, the device, and the request's User-Agent."""

    via: Via
    device: Device
    agent: str = ""


def door(request: Request) -> bool:
    """Whether the request came through the tailnet door: its app says so."""
    return bool(getattr(request.app.state, "door", False))


def refusal(request: Request) -> str | None:
    """None when the main listener takes the act, else the line of its 403."""
    if door(request):
        return None
    client = request.client.host if request.client else ""
    if client not in LOOPBACK:
        return "Only a page on this Mac acts through the board's main address."
    port = request.app.state.facts.port
    own = {f"http://{name}:{port}" for name in LOOPBACK_NAMES}
    origins = [origin.strip().lower() for origin in request.headers.getlist("origin")]
    if len(origins) != 1 or origins[0] not in own:
        return (
            "An act comes only from the board's own page, and this request names "
            "another origin or none."
        )
    sites = {site.strip().lower() for site in request.headers.getlist("sec-fetch-site")}
    if sites - {SAME_ORIGIN}:
        return (
            "An act comes only from the board's own page, and this request comes "
            "from another site."
        )
    return None


def device_of(headers: Headers) -> Device:
    """`phone` when the request names a phone, else `computer`."""
    if headers.get("sec-ch-ua-mobile", "").strip() == "?1":
        return "phone"
    agent = headers.get("user-agent", "")
    return "phone" if PHONE.search(agent) else "computer"


def asker_of(request: Request) -> Asker:
    """Where the request came from."""
    via: Via = "door" if door(request) else "local"
    headers = request.headers
    return Asker(
        via=via, device=device_of(headers), agent=headers.get("user-agent", "")
    )
