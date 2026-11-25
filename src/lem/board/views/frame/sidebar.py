"""The sidebar of every page of a workspace (`board_pages.sidebar`, `notices` and `rail` on
`main`): the repository and the beacon, the notices, what waits for the owner, the views with
their counts, the flags of the folded rail, and the switcher of the workspaces."""

from typing import TYPE_CHECKING

from lem.board.inputs.names import plural
from lem.board.inputs.sidebar import Flag, Sidebar
from lem.board.views.frame import counted, notices, views, waiting

if TYPE_CHECKING:
    from lem.board.inputs.sidebar import Notice
    from lem.board.inputs.switcher import Switcher
    from lem.board.views.world import World

BEACON = "lem serve reads this workspace's files and tells the page each change"


def sidebar(
    world: World,
    counts: counted.Counted,
    backlog: int | None,
    switcher: Switcher,
    problems: tuple[str, ...] = (),
) -> Sidebar:
    """The sidebar; `backlog` is the count of the reviewer's items no task holds (None when
    the backlog did not read)."""
    repo, base = world.place.repo, world.place.base
    found = notices.notices(world, counts)
    return Sidebar(
        repo=repo,
        repo_title=f"{repo} · tasks land on {base}",
        beacon="; ".join(problems) or BEACON,
        beacon_bad=bool(problems),
        notices=found,
        waits_count=counts.waits,
        waits_title=(
            f"{plural(counts.things, 'thing')} you do, in {plural(counts.waits, 'task')}"
        ),
        waits=waiting.waiting(world, counts.stacks),
        views=views.buttons(world, counts, backlog),
        flags=flags(found),
        switcher=switcher,
    )


def flags(found: tuple[Notice, ...]) -> tuple[Flag, ...]:
    """The marks of the folded rail: demo data, the owner away, the tasks stopped."""
    marks = [flag_of(notice) for notice in found if notice.kind in {"demo", "away"}]
    bad = sum(1 for notice in found if notice.kind == "blocked")
    if bad:
        title = (
            f"{plural(bad, 'task')} stopped or with a status no stage writes: unfold the "
            "sidebar"
        )
        marks.append(Flag(kind="bad", look="bad", title=title, count=bad))
    return tuple(marks)


def flag_of(notice: Notice) -> Flag:
    """The rail's mark of demo data or of the owner's away."""
    if notice.kind == "demo":
        said = notice.said
        lowered = said[:1].lower() + said[1:]
        return Flag(kind="demo", title=f"Demo data: {lowered}")
    head, said = notice.head, notice.said
    return Flag(kind="away", look="you", title=f"{head} {said}")


def says(counts: counted.Counted) -> str:
    """What the workspace's tasks do, as the switcher says it: `5 wait for you · 2 build ·
    1 in checks and review`."""
    waits = counts.waits
    head = counted.waits_said(waits) if waits else "nothing waits for you"
    return f"{head} · {runs(counts)}"


def runs(counts: counted.Counted) -> str:
    """What builds and what is checked: `2 build · 1 in checks and review`."""
    building = counts.count("build", "building")
    checks = counts.count("checks")
    verb = "builds" if building == 1 else "build"
    parts = (
        f"{building} {verb}" if building else "",
        f"{checks} in checks and review" if checks else "",
    )
    return " · ".join(part for part in parts if part) or "nothing runs"
