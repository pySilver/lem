"""The one read of a joined machine's board that `lem doctor` makes: whether the agterm on that
machine runs Live sessions, as its board says at `/api/agterm` (`addons/peers/origin.py`).

The address is the machine's door on the owner's tailnet, as the board's relay reads it, over
HTTPS with the certificate checked. The check loads no HTTP library (`test_command.py`), so it
asks with the standard library's client. A board that does not answer says nothing of its agterm,
and the row says why.
"""

from contextlib import closing
from http import HTTPStatus
from http.client import HTTPException, HTTPSConnection
from urllib.parse import urlsplit

import msgspec

from lem.addons.peers import local, requests, tailnet
from lem.kernel.errors import Refusal

AGTERM_PATH = "/api/agterm"
# The board's wait for a joined machine's answer (`addons/peers/look.py`, main 2026-11-25).
ANSWER_WAIT = 4


class Said(msgspec.Struct, frozen=True, kw_only=True):
    """The board's answer: whether its agterm runs Live sessions; null, and why, when it did
    not say."""

    live: bool | None = None
    said: str = ""


def decoded(body: bytes) -> Said:
    """The board's answer, from at most `JSON_CAP` of its bytes."""
    if len(body) > requests.JSON_CAP:
        raise HTTPException("the board's reply exceeds its JSON limit")
    return msgspec.json.decode(body, type=Said)


def asked(base: str) -> Said:
    """The board's answer at `base`; `HTTPException` for any status but 200."""
    split = urlsplit(base)
    made = HTTPSConnection(split.hostname or "", split.port, timeout=ANSWER_WAIT)
    with closing(made) as connection:
        connection.request("GET", AGTERM_PATH, headers={requests.HOP: "1"})
        answer = connection.getresponse()
        body = answer.read(requests.JSON_CAP + 1)
    if answer.status != HTTPStatus.OK:
        raise HTTPException(f"the board answered {answer.status}")
    return decoded(body)


def board_live(name: str, port: int) -> tuple[bool | None, str]:
    """Whether the agterm of the joined machine `name` runs Live sessions, and why the board did
    not say when it is None."""
    try:
        said = asked(tailnet.address(local.status().suffix, name, port))
    except Refusal as refusal:
        return None, refusal.why
    except (OSError, HTTPException, msgspec.DecodeError) as error:
        return None, str(error) or type(error).__name__
    if said.live is None:
        reason = said.said or "no reason"
        return None, f"its agterm did not say its restore mode: {reason}"
    return said.live, ""
