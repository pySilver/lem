"""The board's workspace rows and the add-ons that contribute to a page."""

from dataclasses import replace
from typing import TYPE_CHECKING

import anyio

if TYPE_CHECKING:
    from starlette.requests import Request

    from lem.board import counts
    from lem.board.views import world
    from lem.store.places import Workspace


def local_rows(request: Request, current: counts.Row | None = None) -> counts.Rows:
    """The local rows, with the open page's own counts in its switcher."""
    state = request.app.state
    return state.counts.rows(state.home, state.facts.host, current=current)


def combined(request: Request, own: counts.Rows) -> counts.Rows:
    """Ask the app's peers on the event loop from the page's worker thread."""
    return anyio.from_thread.run(request.app.state.peer_spaces, request, own)


def peer_problem(request: Request) -> str | None:
    """The local peer table's last failure, for a direct request only."""
    if "Lem-Hop" in request.headers:
        return None
    registry = getattr(request.app.state, "peer_registry", None)
    return registry.trouble if registry else None


def with_addons(request: Request, space: Workspace, drawn: world.World) -> world.World:
    """The workspace problems and the Inbox action of the selected task."""
    state = request.app.state
    problems = getattr(state, "inbox_problems", {})
    lines = (
        peer_problem(request),
        problems.get("*"),
        problems.get(drawn.viewer.workspace),
    )
    thread = getattr(state, "inbox_thread", None)
    slug = drawn.viewer.task
    return replace(
        drawn,
        problems=(*drawn.problems, *(line for line in lines if line)),
        inbox_thread=thread(space.state, slug, away=drawn.presence.away)
        if thread and slug
        else None,
    )
