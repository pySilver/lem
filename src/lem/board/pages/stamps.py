"""The stamps of the workspace and task shown by a request."""

from typing import TYPE_CHECKING

from lem.board import watched

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from starlette.requests import Request

    from lem.board.pages.observations import Observation
    from lem.store.places import Workspace


def shown(
    request: Request, state: Path, space: Workspace | None = None
) -> watched.ViewStamp:
    """Stamp the files before the live read, which the page can reuse."""
    slug = request.path_params.get("slug") or request.query_params.get("task")
    acts = acts_of(request, state)
    stamp = watched.look(state, request.app.state.home, slug, acts)
    observe: Callable[[Request, Workspace], Observation] | None = getattr(
        request.app.state, "workspace_inputs", None
    )
    if (
        space is None
        or observe is None
        or getattr(request.app.state, "page_inputs", None) is None
    ):
        return stamp
    found = observe(request, space)
    request.state.workspace_observation = found
    return stamp.with_live(found[0].revision())


def acts_of(request: Request, state: Path) -> str:
    """Pages with a provider require the owner's act revision."""
    server = request.app.state
    if getattr(server, "page_inputs", None) is not None:
        return server.act_revision(state)
    revision: Callable[[Path], str] | None = getattr(server, "act_revision", None)
    return revision(state) if revision else ""
