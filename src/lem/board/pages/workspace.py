"""The workspace facts read for a page, with its merge basis and live sessions."""

from dataclasses import replace
from typing import TYPE_CHECKING

from lem.board.duties import context
from lem.board.duties.memory import MEMORY
from lem.board.pages import snapshot, viewer
from lem.board.views import gather, world
from lem.settings.load import settings_of
from lem.store import tasks

if TYPE_CHECKING:
    from starlette.requests import Request

    from lem.store.places import Workspace


def observe(
    request: Request,
    space: Workspace,
    *,
    live: snapshot.Snapshot | None = None,
) -> snapshot.Snapshot:
    """Read the files, with a fresh live read when the server needs one."""
    state = request.app.state
    settings = settings_of(space.checkout, state.environ, home=state.home).settings
    records = tasks.every(space.state)
    if live is not None:
        return snapshot.with_files(live, settings, records)
    here = context.bound(space, state.environ, state.home)
    demo = (space.state / gather.DEMO).is_file()
    return snapshot.capture(here, settings, records, demo=demo)


def for_page(request: Request, space: Workspace) -> snapshot.Snapshot:
    """Use the fresh files of this request, or read them beside the shared live read."""
    observed = getattr(request.state, "workspace_observation", None)
    if observed is None:
        return observe(request, space)
    found, fresh = observed
    return found if fresh else observe(request, space, live=found)


def read(request: Request, found: snapshot.Snapshot, version: str) -> world.World:
    """Draw the workspace from the same live facts as its version."""
    space = found.here.where
    base = found.settings.branch.base
    wanted = viewer.asking(request, space, base, version, at=found.at)
    wanted = replace(
        wanted,
        git=found.here.ports.git,
        listed=found.listed,
        bases=found.bases,
    )
    drawn = gather.gather(space.checkout, wanted, found.records)
    return replace(
        drawn,
        unknown=None if drawn.demo else found.unknown,
        problems=MEMORY.problems_of(space.checkout),
        running=MEMORY.of(space.checkout).running(),
    )
