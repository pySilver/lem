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
    try:
        body = saved.html(folder, page, asked.digest)
    except FileNotFoundError:
        return Response(status_code=HTTPStatus.NOT_FOUND)
    return Response(
        b"" if request.method == "HEAD" else body,
        headers=headers_for(body, asked.digest),
        media_type="text/html",
    )


def headers_for(body: bytes, digest: str | None) -> dict[str, str]:
    """Bind the browser's navigation and script policy to the verified page."""
    etag = f'"{digest}"'
    return {
        "Content-Security-Policy": csp.policy(body),
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
        "Content-Length": str(len(body)),
        "ETag": etag,
        "Server-Timing": f"card-digest;desc={etag}",
    }


def redirected(request: Request) -> RedirectResponse:
    """Keep the card's canonical path and its query."""
    url = request.url
    path = f"{url.path}/"
    query = f"?{url.query}" if url.query else ""
    return RedirectResponse(path + query, status_code=HTTPStatus.FOUND)
