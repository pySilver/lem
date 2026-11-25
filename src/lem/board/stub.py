"""What an address of the board answers until the step of the rebuild that builds it: 501, with
the step's id, as a command of the tree refuses `not-built`."""

from functools import partial
from http import HTTPStatus
from typing import TYPE_CHECKING

import msgspec
from starlette.responses import Response
from starlette.routing import Route

if TYPE_CHECKING:
    from starlette.requests import Request

DESIGN = "docs/plans/2026-11-25-lem-built-again.md"


class NotBuilt(msgspec.Struct, frozen=True, kw_only=True):
    """The answer of an address not built yet: the step that builds it, and why."""

    step: str
    why: str


async def not_built(request: Request, *, step: str) -> Response:
    """Answer 501, naming the step that builds the address."""
    method = request.method
    path = request.url.path
    address = f"{method} {path}"
    said = NotBuilt(
        step=step,
        why=f"{address} is not built yet: the step `{step}` builds it ({DESIGN}, part 9)",
    )
    return Response(
        msgspec.json.encode(said),
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        media_type="application/json",
    )


def routes(step: str, method: str, *paths: str) -> tuple[Route, ...]:
    """The addresses `paths` of `method`, each answering that `step` builds it; a GET answers
    HEAD too."""
    answer = partial(not_built, step=step)
    return tuple(Route(path, answer, methods=[method]) for path in paths)
