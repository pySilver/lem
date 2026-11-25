"""Who asks for an act of the board: the listener it came to, the device, and the browser's own
words. The listener checks where the request came from.
"""

import re
from typing import TYPE_CHECKING, Literal

from lem.board import listener
from lem.records.base import Frozen

if TYPE_CHECKING:
    from starlette.datastructures import Headers
    from starlette.requests import Request

type Via = Literal["local", "door"]
type Device = Literal["phone", "computer"]

# A request that names a phone: the client hint of a mobile browser, or a User-Agent that names
# an iPhone, an iPad or Android. A phone in a desktop mode says it is a computer, and the record
# keeps the User-Agent whole beside it.
PHONE = re.compile(r"\b(iPhone|iPad|Android)\b")


class Asker(Frozen, frozen=True, kw_only=True):
    """Where an act came from: the listener, the device, and the request's User-Agent."""

    via: Via
    device: Device
    agent: str = ""


def device_of(headers: Headers) -> Device:
    """`phone` when the request names a phone, else `computer`."""
    if headers.get("sec-ch-ua-mobile", "").strip() == "?1":
        return "phone"
    agent = headers.get("user-agent", "")
    return "phone" if PHONE.search(agent) else "computer"


def asker_of(request: Request) -> Asker:
    """Where the request came from."""
    via: Via = "door" if listener.at_door(request) else "local"
    headers = request.headers
    return Asker(
        via=via, device=device_of(headers), agent=headers.get("user-agent", "")
    )
