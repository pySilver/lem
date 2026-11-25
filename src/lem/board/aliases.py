"""The addresses no page has, which go to the page they mean (`Handler.answer` on `main`): the
machine's other name goes to the same page under its name in every address; an address with no
machine's name in it goes to the same page under it, or to the workspace's Tasks for a view no
page has; and a workspace's address with no final slash gets it. Anything else is 404.

These are the last routes of the app, so that every page, act and file of the board is matched
first.
"""

from functools import partial
from http import HTTPStatus
from typing import TYPE_CHECKING
from urllib.parse import quote

import msgspec
from starlette.responses import PlainTextResponse, RedirectResponse, Response
from starlette.routing import Route

from lem.board import workspaces

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from starlette.requests import Request

    from lem.board.facts import Facts

# The views of a workspace, by the first word after its name (`serve.PAGES` on `main`).
NO_PAGE = "No page at this address on this server."
VIEWS = ("", "waits", "backlog", "activity", "done", "new", "stream", "tasks")


def under(host: str, rest: str, query: str) -> str:
    """The address `rest` under the machine's name, with its query."""
    address = f"/{quote(host)}/{quote(rest)}"
    return f"{address}?{query}" if query else address


def target(facts: Facts, asked: Asked, listed: Callable[[str], bool]) -> str | None:
    """Where the address `asked` goes, None when nowhere: `listed(name)` says whether a
    workspace of that name is on the list."""
    first, rest = asked.first, asked.rest
    if first in facts.aliases:
        return under(facts.host, rest, asked.query)
    if first == facts.host:
        lone = "/" not in rest and listed(rest)
        return under(first, f"{rest}/", "") if lone else None
    if not listed(first):
        return None
    if rest.split("/")[0] in VIEWS:
        return under(facts.host, f"{first}/{rest}", asked.query)
    return under(facts.host, f"{first}/", "")


async def gone_to(request: Request) -> Response:
    """The page an address with no page means, or 404."""
    state = request.app.state
    asked = Asked(
        first=request.path_params["first"],
        rest=request.path_params.get("rest", ""),
        query=request.url.query,
    )
    looked = partial(listed, state.home, state.facts.host)
    to = target(state.facts, asked, looked)
    if to is None:
        return PlainTextResponse(NO_PAGE, status_code=HTTPStatus.NOT_FOUND)
    return RedirectResponse(to, HTTPStatus.FOUND)


def listed(home: Path, host: str, name: str) -> bool:
    """Whether the workspace `name` is on the list and still has Lem set up."""
    return workspaces.found(home, host, name) is not None


class Asked(msgspec.Struct, frozen=True, kw_only=True):
    """An address no page has: its first word, the rest, and its query."""

    first: str
    rest: str = ""
    query: str = ""


ROUTES = (
    Route("/{first}", gone_to, methods=["GET"]),
    Route("/{first}/{rest:path}", gone_to, methods=["GET"]),
)
