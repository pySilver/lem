"""What a request of a page says of who asks, for the page's `Viewer` (`board/inputs/layout.py`):
the board's own state from its one cookie, whether the page is for this Mac, whether it may act,
and whether it is the Hotwire Native app (`serve.prefs_of` and `board_pages.Ctx` on `main`).

The cookie `lem_board` holds the folded columns, the folded sidebar, the panel's width and
whether it is expanded, and whether a task's header shows its details on a phone, as JSON; a
cookie that does not read, or is nested past what Python reads, is no preference.
"""

import re
from http.cookies import CookieError, SimpleCookie
from typing import TYPE_CHECKING
from urllib.parse import unquote

import msgspec

from lem.board import listener

if TYPE_CHECKING:
    from starlette.requests import HTTPConnection

COOKIE = "lem_board"
# The panel's widths a dragged width may take, in px: a guess at what any screen and any panel
# holds (`serve.PANEL_WIDTHS` on `main`).
NARROWEST = 300
WIDEST = 4000
NATIVE = re.compile(r"\b(Turbo|Hotwire) Native\b")
# The columns a fold may name (`board_model.LANE` on `main`).
COLUMNS = ("you", "build", "checks", "done")


class Prefs(msgspec.Struct, frozen=True, kw_only=True):
    """The board's own state, as the cookie holds it, each part checked."""

    folded: tuple[str, ...] = ()
    rail: bool = False
    pw: int | None = None
    full: bool = False
    head: bool = False


class Asker(msgspec.Struct, frozen=True, kw_only=True):
    """Who asks for a page: whether it is for this Mac (the agterm jump), whether it may act
    (on this Mac or through the door), whether it is the Hotwire Native app, and the cookie."""

    local: bool
    may_act: bool
    native: bool
    prefs: Prefs


def checked(given: object) -> Prefs:
    """The parts of the cookie's JSON that hold, each dropped that does not."""
    if not isinstance(given, dict):
        return Prefs()
    folded = given.get("folded")
    width = given.get("pw")
    fits = isinstance(width, int) and not isinstance(width, bool)
    return Prefs(
        folded=tuple(one for one in folded if one in COLUMNS)
        if isinstance(folded, list)
        else (),
        rail=given.get("rail") is True,
        pw=width if fits and NARROWEST <= width <= WIDEST else None,
        full=given.get("full") is True,
        head=given.get("head") is True,
    )


def prefs_of(header: str | None) -> Prefs:
    """The board's own state from the request's `Cookie`; none when it does not read."""
    try:
        jar = SimpleCookie(header or "")
    except CookieError:
        return Prefs()
    morsel = jar.get(COOKIE)
    if morsel is None:
        return Prefs()
    try:
        given = msgspec.json.decode(unquote(morsel.value))
    except msgspec.DecodeError, RecursionError:
        return Prefs()
    return checked(given)


def asker_of(request: HTTPConnection) -> Asker:
    """Who asks for the page of `request`."""
    door = listener.at_door(request)
    local = not door and listener.from_here(request)
    agent = request.headers.get("user-agent", "")
    return Asker(
        local=local,
        may_act=door or local,
        native=bool(NATIVE.search(agent)),
        prefs=prefs_of(request.headers.get("cookie")),
    )
