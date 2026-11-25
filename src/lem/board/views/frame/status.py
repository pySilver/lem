"""The status bar (`board_pages.statusbar` on `main`): what did not read, when the workspace's
files were read and how many entries their journals hold, and the look at the forge."""

from typing import TYPE_CHECKING

from lem.board.inputs import clock
from lem.board.inputs.layout import Statusbar

if TYPE_CHECKING:
    from lem.board.views.world import World

ASKS = "The board asks GitHub itself"
DEMO = (
    "example tasks: no forge is asked",
    "A board of example tasks asks GitHub nothing",
)


def statusbar(world: World, problems: tuple[str, ...] = ()) -> Statusbar:
    """The status bar: what did not read, when the files were read, how many entries, and
    the look at the forge."""
    entries = sum(len(seen.record.journal) for seen in world.tasks)
    noun = "entry" if entries == 1 else "entries"
    said = forge_said(world)
    viewer = world.viewer
    return Statusbar(
        problems=problems,
        read=clock.gone(world.clock.now, world.clock.now),
        events=f"{entries} {noun}",
        forge=said[0],
        forge_title=said[1],
        forge_bad=said[2],
        live=f"live-{viewer.host}-{viewer.workspace}",
    )


def forge_said(world: World) -> tuple[str, str, bool]:
    """The look at the forge in words, its hover, and whether it failed."""
    looked, problem = world.forge.looked, world.forge.problem
    if problem is not None:
        return problem, f"{ASKS} while a pull request is open", True
    if looked is not None:
        ago = clock.ago((world.clock.now - looked).total_seconds())
        title = (
            f"{ASKS}, a few minutes apart, while a pull request is open; a merge or a close "
            "there is recorded at once, and the task's session is woken"
        )
        return f"the board looked at GitHub {ago}", title, False
    if world.demo:
        return DEMO[0], DEMO[1], False
    title = f"{ASKS}, a few minutes apart, while a task is open with a pull request"
    return "GitHub was not asked yet", title, False
