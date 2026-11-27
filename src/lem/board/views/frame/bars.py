"""The page's head, the phone's bar and the bar above the view (`board_pages.layout` and `topbar`
on `main`): the title with what builds and what waits, the stream, the way to a new task where the
page may act, and the chips of the base branch, the pull requests proposed, the look at GitHub
and the tasks landed today."""

from typing import TYPE_CHECKING

from lem.board.inputs.layout import Head, Phonebar, Topbar
from lem.board.inputs.names import title_of
from lem.board.views.frame import counted, forge

if TYPE_CHECKING:
    from lem.board.views.world import World

DEMO = "DEMO · "


def head(world: World, title: str, counts: counted.Counted, *, joined: bool) -> Head:
    """The page's head: its title, its stream and version, and the agterm jump on this Mac."""
    viewer = world.viewer
    mark = DEMO if world.demo else ""
    repo = f"{viewer.host}/{viewer.workspace}" if joined else world.place.repo
    if viewer.task is None:
        builds = counts.count("build", "building")
        named = (
            f"{mark}{title} · Lem · {repo} · {builds} build · {counts.waits} for you"
        )
    else:
        named = task_title(counts, viewer.task, mark, repo)
    return Head(
        title=named,
        stream=f"{viewer.base}/stream",
        version=world.version,
        jump=f"{viewer.base}/agterm" if viewer.local else None,
    )


def task_title(counts: counted.Counted, slug: str, mark: str, repo: str) -> str:
    """The title of a page whose panel shows the task `slug`."""
    label = label_of(counts, slug)
    title = title_of(slug)
    return f"{mark}{title} · {label} · Lem · {repo}"


def label_of(counts: counted.Counted, slug: str) -> str:
    """The words of the state of the task `slug`, or that it has none yet."""
    labels = (
        where.label for seen, where in counts.placed if seen.record.task.slug == slug
    )
    return next(labels, "no state yet")


def phonebar(world: World, counts: counted.Counted) -> Phonebar:
    """The bar at the top of a phone."""
    workspace = world.viewer.workspace
    title = f"{workspace} · demo data" if world.demo else workspace
    said = counted.tasks_said(counts.waits)
    return Phonebar(
        title=title,
        waits=counts.waits,
        waits_label=f"{said}: open the list",
        new_task=new_task(world),
    )


def topbar(world: World, title: str, summary: str) -> Topbar:
    """The bar above the view."""
    return Topbar(
        title=title,
        summary=summary,
        chips=forge.chips(world),
        new_task=new_task(world),
    )


def new_task(world: World) -> str | None:
    """The way to a new task, where the page may act."""
    viewer = world.viewer
    return f"{viewer.base}/new" if viewer.may_act else None
