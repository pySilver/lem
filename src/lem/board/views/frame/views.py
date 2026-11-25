"""The views of a workspace in the sidebar (`board_pages.VIEWS` and the sidebar's buttons on
`main`): Tasks, Waits for you, Backlog, Activity, each with its key, its count and the hover of
the folded rail; and the switcher's line when the machine has no other workspace."""

from types import MappingProxyType
from typing import TYPE_CHECKING, NamedTuple

from lem.board.inputs.sidebar import ViewButton
from lem.board.inputs.switcher import Switcher
from lem.board.views.frame import counted

if TYPE_CHECKING:
    from lem.board.views.world import World


class Spec(NamedTuple):
    """A view: its key, the end of its address, its words, its icon, and its key on the
    keyboard."""

    key: str
    path: str
    label: str
    icon: str
    kbd: str


WAITS = "waits"
BACKLOG = "backlog"
VIEWS = (
    Spec("tasks", "", "Tasks", "square-kanban", "T"),
    Spec(WAITS, WAITS, "Waits for you", "inbox", "W"),
    Spec(BACKLOG, BACKLOG, "Backlog", "list-check", "B"),
    Spec("activity", "activity", "Activity", "list-timeline", "A"),
)
BACKLOG_COUNT = "The reviewer's items that wait for your start or drop"


def buttons(
    world: World, counts: counted.Counted, backlog: int | None
) -> tuple[ViewButton, ...]:
    """The four views, the one shown marked: Tasks counts every task that did not end, and
    `backlog` is the Backlog key's count."""
    opened = len(counts.placed) - counts.count("done")
    numbers = MappingProxyType({"tasks": opened, WAITS: counts.waits, BACKLOG: backlog})
    found = ((spec, numbers.get(spec.key)) for spec in VIEWS)
    return tuple(button(world, spec, count, counts) for spec, count in found)


def button(
    world: World, spec: Spec, count: int | None, counts: counted.Counted
) -> ViewButton:
    """One view's button."""
    waits = spec.key == WAITS
    counted_backlog = spec.key == BACKLOG and count is not None
    base = world.viewer.base
    return ViewButton(
        key=spec.key,
        label=spec.label,
        icon=spec.icon,
        href=f"{base}/{spec.path}",
        kbd=spec.kbd,
        rail_title=rail_title(counts) if waits else f"{spec.label} · key {spec.kbd}",
        count=count,
        count_title=BACKLOG_COUNT if counted_backlog else None,
        current=world.viewer.view == spec.key,
        look="you" if waits and counts.waits else None,
    )


def rail_title(counts: counted.Counted) -> str:
    """The hover of Waits for you on the folded rail."""
    if not counts.waits:
        return "Nothing waits for you"
    return counted.tasks_said(counts.waits)


def lone(world: World, says: str) -> Switcher:
    """The workspace's name, counts and path when it is the machine's only one."""
    name = world.viewer.workspace
    path = world.place.path
    return Switcher(name=name, title=f"{name}: {says}\n{path}")
