"""The machine's workspaces in the index and in the switcher on a workspace page."""

from typing import TYPE_CHECKING

from lem.board.counts import Row
from lem.board.inputs import switcher
from lem.board.inputs.parts import Chip
from lem.board.views.frame.counted import counted

if TYPE_CHECKING:
    from lem.board.counts import Rows
    from lem.board.inputs.text import Look
    from lem.board.views.world import World


def says(row: Row) -> str:
    """The workspace's counts, or the reason they could not be read."""
    if row.reachable is False:
        return f"Not reachable: {row.said}"
    if row.problem and row.waits is None:
        return row.problem
    counts = (
        f"{row.waits} wait for you · {row.building} building"
        f" · {row.checks} in checks and review"
    )
    return f"{counts} · {row.problem}" if row.problem else counts


def look(row: Row) -> Look | None:
    """The owner's color when something waits, the color of trouble when the counts are missing."""
    if row.waits:
        return "you"
    if row.reachable is False or (row.problem and row.waits is None):
        return "bad"
    return None


def index(rows: Rows, host: str, *, problem: str | None = None) -> switcher.Workspaces:
    """The index, with workspaces that wait for the owner first. With two or more machines,
    each box names its machine, under which the page groups it, and its workspace alone."""
    joined = any(row.host != host for row in rows)
    boxes = tuple(
        switcher.Box(
            id=row.url or row.host,
            name=(row.name or row.host) if joined else row.name,
            host=row.host if joined else None,
            path=row.path,
            href=None if row.reachable is False else row.url,
            waits=bool(row.waits),
            chips=(Chip(label=says(row), look=look(row)),),
        )
        for row in rows
    )
    return switcher.Workspaces(
        host=host, ask=problem or "Select a workspace.", boxes=boxes
    )


def menu(
    rows: Rows, current: str, host: str, *, joined: bool = False
) -> switcher.Switcher | None:
    """The switcher when the board has another workspace or machine."""
    joined = joined or any(row.host != host for row in rows)
    if len(rows) <= 1:
        return (
            switcher.Switcher(name=current, host=host, title=f"{host}/{current}")
            if joined
            else None
        )
    spaces = tuple(
        switcher.Space(
            id=row.url or row.host,
            host=row.host if joined else None,
            reachable=row.reachable is not False,
            name=row.name,
            path=row.path,
            href=row.url,
            here=(row.name, row.host) == (current, host),
            says=says(row),
            waits=bool(row.waits),
        )
        for row in rows
    )
    waiting = sum(space.waits for space in spaces if not space.here)
    group = switcher.Group(head="Workspaces", spaces=spaces)
    return switcher.Switcher(
        name=current,
        host=host if joined else None,
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
