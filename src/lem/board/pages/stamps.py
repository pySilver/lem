"""The stamps of the workspace and task shown by a request."""

from typing import TYPE_CHECKING

from lem.board import watched

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from starlette.requests import Request


def shown(request: Request, state: Path) -> watched.ViewStamp:
    """Read the version before a page gathers its records or a stream starts its poll."""
    slug = request.path_params.get("slug") or request.query_params.get("task")
    revision: Callable[[Path], str] = request.app.state.act_revision
    return watched.look(state, request.app.state.home, slug, revision(state))
