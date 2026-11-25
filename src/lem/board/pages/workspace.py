"""The workspace facts read for a page, with its merge basis and live sessions."""

from dataclasses import replace
from typing import TYPE_CHECKING

from lem.app.owner import looking, sessions
from lem.board.duties import context
from lem.board.duties.memory import MEMORY
from lem.board.pages import viewer
from lem.board.views import gather, world
from lem.store import tasks

if TYPE_CHECKING:
    from starlette.requests import Request

    from lem.settings.team import Branch
    from lem.store.places import Workspace


def read(
    request: Request, space: Workspace, branch: Branch, version: str
) -> world.World:
    """Read the records once for the terminal, the base and the page."""
    here = context.bound(space, request.app.state.environ, request.app.state.home)
    records = tasks.every(space.state)
    wanted = viewer.asking(request, here, branch.base, version)
    shown, unknown = (
        (None, None)
        if (space.state / "demo").is_file()
        else sessions.sessions_of(here, wanted.clock.now, records)
    )
    wanted = replace(
        wanted,
        listed=None if unknown else shown,
        basis=looking.basis_of(here, branch, records),
    )
    return replace(
        gather.gather(space.checkout, wanted, records),
        unknown=unknown,
        problems=MEMORY.problems_of(space.checkout),
        running=MEMORY.of(space.checkout).running(),
    )
