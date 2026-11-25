"""The tab Timeline of a task, `/HOST/WORKSPACE/tasks/SLUG/timeline` (`board_task.timeline_tab`
and `feed_card` on `main`): the card of the task's time, and its rows, the newest first. The
newest move's words are the large card's on the Overview, so its row names only the state.

A task whose journal retention folded into one summary has neither: its tab says that they went
with its events, and links to its Artifacts.
"""

from typing import TYPE_CHECKING

from lem.board.inputs.task.timeline import Timeline
from lem.board.views import owed, standing
from lem.board.views.activity import feed, happenings
from lem.board.views.panel import pruned
from lem.board.views.timeline import card, frame

if TYPE_CHECKING:
    from lem.board.inputs.activity import Happened
    from lem.board.views.world import Seen, World


def timeline(world: World, slug: str) -> Timeline:
    """The tab of the task `slug`."""
    seen = owed.seen(world, slug)
    record = seen.record
    if pruned.summary_of(seen) is not None:
        return Timeline(went=pruned.went(world, seen, "timeline"))
    look = standing.standing(seen, owed.of_task(world, slug)).look
    drawn = frame.frame_of(record, world.clock.now)
    rows = rows_of(world, seen)
    return Timeline(
        time=card.time_card(record, look, drawn, world.clock),
        events=feed.count_line(len(rows)),
        feed=rows[: feed.NEWEST],
    )


def rows_of(world: World, seen: Seen) -> tuple[Happened, ...]:
    """The task's rows, the newest first."""
    told = happenings.of(seen)
    newest = newest_state(told)
    placed = reversed(tuple(enumerate(told)))
    return tuple(row_at(world, place, row, newest) for place, row in placed)


def newest_state(told: tuple[happenings.Happening, ...]) -> int:
    """The place of the task's newest move, or -1 with none."""
    states = [place for place, row in enumerate(told) if row.state]
    return states[-1] if states else -1


def row_at(
    world: World, place: int, row: happenings.Happening, newest: int
) -> Happened:
    """A row of the task's feed; the newest move names only its state."""
    if place == newest:
        bare = row.told._replace(text="", sub="")
        row = row._replace(told=bare)
    return feed.row(world, None, f"tev-{place}", row)


def tab(world: World, seen: Seen) -> Timeline:
    """The tab Timeline of the task of `seen`, as the panel takes a tab."""
    return timeline(world, seen.record.task.slug)
