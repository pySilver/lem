"""Read a device's request body up to the board's limit."""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from starlette.requests import Request

# What a device posts, at most, in bytes (`push.MAX_BODY` on main).
MOST = 4096


def refused() -> Refusal:
    """The answer to an empty body or one past the limit."""
    return Refusal(
        "no-json", f"the request carries no JSON of at most {MOST} bytes", ""
    )


def declared(request: Request) -> int:
    """The declared length, or the limit when the request came without one."""
    try:
        return int(request.headers.get("content-length", str(MOST)))
    except ValueError as error:
        raise refused() from error


async def read(request: Request) -> bytearray:
    """Refuse a declared excess before reading, and stop at the first excess chunk."""
    if not 0 < declared(request) <= MOST:
        raise refused()
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > MOST:
            raise refused()
        body.extend(chunk)
    if not body:
        raise refused()
    return body
