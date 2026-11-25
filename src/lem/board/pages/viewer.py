"""The viewer of a page, from the route, listener and cookie of its request."""

from datetime import UTC
from typing import TYPE_CHECKING, get_args

from lem.board import prefs
from lem.board.acts.back import base_of
from lem.board.inputs.layout import Viewer
from lem.board.inputs.text import View
from lem.board.views import ask, world
from lem.kernel import clock

if TYPE_CHECKING:
    from datetime import datetime

    from starlette.requests import Request

    from lem.store.places import Workspace

VIEWS: tuple[View, ...] = get_args(View.__value__)


def viewer_of(request: Request) -> Viewer:
    """The view under the panel and the task, tab and file it opens."""
    who = prefs.asker_of(request)
    route = request.state.page_route
    path = request.path_params
    under = request.query_params.get("in") if "slug" in path else route
    return Viewer(
        host=path["host"],
        workspace=path["workspace"],
        base=base_of(request),
        view=next((view for view in VIEWS if view == under), "tasks"),
        task=path.get("slug"),
        tab="artifacts" if route == "artifact" else route,
        path=path.get("path"),
        key=request.query_params.get("key"),
        words=request.query_params.get("words"),
        local=who.local,
        may_act=who.may_act,
        native=who.native,
        folded=who.prefs.folded,
        rail=who.prefs.rail,
        full=who.prefs.full,
        width=who.prefs.pw,
        head_open=who.prefs.head,
    )


def asking(
    request: Request,
    space: Workspace,
    base: str | None,
    version: str,
    *,
    at: datetime | None = None,
) -> ask.Ask:
    """The place and viewer of a workspace at this request."""
    checkout = space.checkout
    now = (at or clock.now()).astimezone()
    return ask.Ask(
        viewer=viewer_of(request),
        clock=world.Clock(now=now, zone=now.tzinfo or UTC),
        version=version,
        place=world.Place(
            repo=checkout.name, base=base or "the base branch", path=str(checkout)
        ),
        home=request.app.state.home,
    )
