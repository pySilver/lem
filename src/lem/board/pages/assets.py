"""The same installed assets at /assets and /HOST/assets."""

from http import HTTPStatus
from typing import TYPE_CHECKING

from starlette.exceptions import HTTPException
from starlette.staticfiles import StaticFiles

from lem.kernel import paths

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.responses import Response

ASSETS = paths.root() / "skills" / "lem" / "assets"
FILES = StaticFiles(directory=ASSETS)


async def on_host(request: Request) -> Response:
    """Serve the asset only for this machine's address."""
    if request.path_params["host"] != request.app.state.facts.host:
        raise HTTPException(HTTPStatus.NOT_FOUND)
    return await FILES.get_response(request.path_params["path"], request.scope)
