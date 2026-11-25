"""The file the address of the tab Artifacts names (`world.viewer.path`), only when it is one of
the task's, so that nothing outside its files is shown by a name a request gives
(`artifacts.one` on `main`); and the words of the panel of an address that names none."""

from typing import TYPE_CHECKING

from lem.board.inputs.names import title_of
from lem.board.views.artifacts.listing import entries_of

if TYPE_CHECKING:
    from lem.board.views.world import Seen, World


def chosen_of(world: World, seen: Seen) -> str | None:
    """The file the address names, when it is one of the task's."""
    path = world.viewer.path if world.viewer.tab == "artifacts" else None
    listed = {entry.path for entry in entries_of(seen)}
    return path if path in listed else None


def missing(world: World, seen: Seen) -> str | None:
    """What the panel says of an address that names no file of the task, or None."""
    path = world.viewer.path if world.viewer.tab == "artifacts" else None
    if path is None or chosen_of(world, seen) is not None:
        return None
    return f"The task {title_of(seen.record.task.slug)} has no file {path!r}."
