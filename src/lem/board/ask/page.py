"""The card's original HTML, with the board's content policy."""

from http import HTTPStatus
from typing import TYPE_CHECKING

from starlette.responses import RedirectResponse, Response

from lem.board.ask import csp, saved, where

if TYPE_CHECKING:
    from starlette.requests import Request


def endpoint(request: Request) -> Response:
    """Give the same page as the overlay, or the headers its scripts can see."""
    folder, page, asked = where.located(request)
    if not request.url.path.endswith("/"):
        return redirected(request)
    headers = {
        "Content-Security-Policy": csp.policy(),
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
        "ETag": f'"{asked.digest}"',
    }
    try:
        body = saved.html(folder, page, asked.digest)
    except FileNotFoundError:
        return Response(status_code=HTTPStatus.NOT_FOUND)
    headers["Content-Length"] = str(len(body))
    return Response(
        b"" if request.method == "HEAD" else body,
        headers=headers,
        media_type="text/html",
    )


def redirected(request: Request) -> RedirectResponse:
    """Keep the card's canonical path and its query."""
    url = request.url
    path = f"{url.path}/"
    query = f"?{url.query}" if url.query else ""
    return RedirectResponse(path + query, status_code=HTTPStatus.FOUND)
