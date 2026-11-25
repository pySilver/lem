"""The feed: what happened, the newest first, as rows of the page (`board_model.feed`,
`board_pages.feed_rows` and `board_task.feed_card` on `main`). A time sorts, and in one moment
the later row comes first. A feed shows its newest 200 rows and counts them all.

Each row keeps its id while rows come after it: the Activity names the task and the row's place
among the task's rows (`ev-SLUG-N`), a task's own feed the place alone (`tev-N`).
"""

from typing import TYPE_CHECKING

from lem.board.inputs import clock, names
from lem.board.inputs.activity import Happened
from lem.board.inputs.parts import Link
from lem.board.views.activity import happenings

if TYPE_CHECKING:
    from collections.abc import Iterator
    from datetime import datetime

    from lem.board.views.world import Seen, World

    # A row with what sorts it: its moment, its task's place in the world and its own place.
    type Placed = tuple[happenings.Happening, int, int, Seen]

# How many rows a feed shows, the newest (`FEED_NEWEST` on `main`).
NEWEST = 200


def everything(world: World) -> tuple[tuple[Happened, ...], int]:
    """Every task's rows, the newest first, and how many there are."""
    placed = sorted(placed_of(world), key=newest, reverse=True)
    rows = tuple(
        row(world, seen, ident(seen, place), happening)
        for happening, _, place, seen in placed[:NEWEST]
    )
    return rows, len(placed)


def placed_of(world: World) -> Iterator[Placed]:
    """Each task's rows, with their task's place in the world and their own."""
    for index, seen in enumerate(world.tasks):
        for place, happening in enumerate(happenings.of(seen)):
            yield happening, index, place, seen


def newest(placed: Placed) -> tuple[datetime, int, int]:
    """What sorts a row: its moment, then its task's place, then its own."""
    happening, index, place, _ = placed
    return happening.at, index, place


def ident(seen: Seen, place: int) -> str:
    """The id of a task's row in the Activity."""
    slug = seen.record.task.slug
    return f"ev-{slug}-{place}"


def count_line(count: int) -> str:
    """`118 events`, with `the newest 200` when the feed shows fewer than it counts."""
    counted = names.plural(count, "event")
    if count <= NEWEST:
        return counted
    return f"{counted} · the newest {NEWEST}"


def row(
    world: World, seen: Seen | None, named: str, happening: happenings.Happening
) -> Happened:
    """A row; with `seen`, linked to its task's Timeline over the Activity."""
    told = happening.told
    moment = clock.fixed(happening.at, world.clock.now, world.clock.zone)
    return Happened(
        id=named,
        look=told.look,
        icon=told.icon,
        task=None if seen is None else task_link(world, seen),
        head=told.head,
        text=told.text or None,
        mono=told.mono,
        sub=told.sub or None,
        at=moment,
    )


def task_link(world: World, seen: Seen) -> Link:
    """The link of a row's task, which opens its Timeline in the panel over the Activity."""
    slug = seen.record.task.slug
    title = names.title_of(slug)
    href = names.task_href(world.viewer.base, slug, "timeline", under="activity")
    return Link(href=href, label=title, title=title, frame=True)
