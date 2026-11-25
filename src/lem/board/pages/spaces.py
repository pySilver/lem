"""The machine's workspaces in the index and in the switcher on a workspace page."""

from typing import TYPE_CHECKING

from lem.board.counts import Row
from lem.board.inputs import switcher
from lem.board.inputs.parts import Chip
from lem.board.views.frame.counted import counted

if TYPE_CHECKING:
    from lem.board.counts import Rows
    from lem.board.views.world import World


def says(row: Row) -> str:
    """The workspace's counts, or the reason they could not be read."""
    if row.problem:
        return row.problem
    return f"{row.waits} wait for you · {row.building} building · {row.checks} in checks and review"


def index(rows: Rows, host: str) -> switcher.Workspaces:
    """The index, with workspaces that wait for the owner first."""
    ordered = sorted(rows, key=lambda row: (not row.waits, row.name))
    boxes = tuple(
        switcher.Box(
            id=row.name,
            name=row.name,
            path=row.path,
            href=row.url,
            waits=bool(row.waits),
            chips=(Chip(label=says(row)),),
        )
        for row in ordered
    )
    return switcher.Workspaces(host=host, ask="Select a workspace.", boxes=boxes)


def menu(rows: Rows, current: str) -> switcher.Switcher | None:
    """The switcher when the machine has another workspace."""
    if len(rows) <= 1:
        return None
    spaces = tuple(
        switcher.Space(
            id=row.name,
            name=row.name,
            path=row.path,
            href=row.url,
            here=row.name == current,
            says=says(row),
            waits=bool(row.waits),
        )
        for row in rows
    )
    others = (row for row in rows if row.name != current)
    waiting = sum(bool(row.waits) for row in others)
    group = switcher.Group(head="Workspaces", spaces=spaces)
    return switcher.Switcher(
        name=current,
        title="Workspaces",
        groups=(group,),
        waiting=waiting,
        menu="Workspaces",
        every="All workspaces",
    )


def current(world: World) -> Row:
    """The current workspace counts from the records used for its sidebar."""
    found = counted(world)
    building = found.count("build", "building")
    checks = found.count("checks")
    viewer = world.viewer
    return Row(
        name=viewer.workspace,
        path=world.place.path,
        host=viewer.host,
        url=f"{viewer.base}/",
        waits=found.waits,
        building=building,
        checks=checks,
        running=building + checks,
    )
