"""Render typed board inputs with Jinja and fail on a missing field."""

from http import HTTPStatus
from types import MappingProxyType
from typing import TYPE_CHECKING

import jinja2
from starlette.responses import HTMLResponse, RedirectResponse, Response

from lem.board.inputs.names import task_href
from lem.board.inputs.switcher import Workspaces
from lem.board.pages import printing

if TYPE_CHECKING:
    import msgspec

    from lem.board.inputs.page import Page

ENV = jinja2.Environment(
    loader=jinja2.PackageLoader("lem.board", "templates"),
    autoescape=True,
    undefined=jinja2.StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True,
)
ENV.filters.update(
    address=printing.address,
    inline=printing.inline,
    milliseconds=printing.milliseconds,
    read_key=printing.read_key,
    task_address=task_href,
)
SYMBOLS = printing.icons()
HEADERS = MappingProxyType(
    {
        "Cache-Control": "no-store",
        "Vary": "Turbo-Frame",
        "Referrer-Policy": "same-origin",
        "X-Content-Type-Options": "nosniff",
    }
)


def section(name: str, board: msgspec.Struct) -> str:
    """The HTML of one template and its input."""
    return ENV.get_template(name).render(board=board, symbols=SYMBOLS)


def page(board: Page | Workspaces, *, fragment: bool = False) -> Response:
    """A workspace page, its Turbo frame, or the workspace index."""
    if isinstance(board, Workspaces):
        return workspaces(board)
    name = (
        "fragment.html" if fragment and not board.frame.viewer.native else "page.html"
    )
    status = HTTPStatus.OK
    if board.panel and board.panel.missing and not board.panel.missing.found:
        status = HTTPStatus.NOT_FOUND
    return HTMLResponse(section(name, board), status_code=status, headers=HEADERS)


def workspaces(board: Workspaces) -> Response:
    """Take the owner straight to the only workspace when it has an address."""
    if len(board.boxes) == 1:
        href = board.boxes[0].href
        if href:
            return RedirectResponse(
                printing.address(href), status_code=HTTPStatus.FOUND
            )
    return HTMLResponse(section("workspaces.html", board), headers=HEADERS)
