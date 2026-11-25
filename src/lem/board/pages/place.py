"""The workspace a page's address names, `/HOST/WORKSPACE/...`: a host that is not this
machine's, or a workspace that is not on the list, is 404."""

from http import HTTPStatus
from typing import TYPE_CHECKING

from starlette.exceptions import HTTPException

from lem.board import workspaces

if TYPE_CHECKING:
    from starlette.requests import Request

    from lem.store.places import Workspace


def workspace(request: Request) -> Workspace:
    """The workspace of the request's address."""
    state = request.app.state
    host = request.path_params["host"]
    name = request.path_params["workspace"]
    found = None
    if host == state.facts.host:
        found = workspaces.found(state.home, host, name)
    if found is None:
        raise HTTPException(
            HTTPStatus.NOT_FOUND, f"no workspace {name} on the board of {host}"
        )
    return found
