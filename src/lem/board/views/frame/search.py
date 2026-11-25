"""The rows of the search over every card of a workspace that are tasks (`board_model.search_rows`
on `main`): the tasks of the columns that have not ended, each column in the kanban's order, then
the parked tasks, then every ended task, the newest first, also those Done draws no card for.
The backlog's rows come after them (`views/backlog/search.py`)."""

from itertools import chain
from typing import TYPE_CHECKING

from lem.board.inputs.names import task_href, title_of
from lem.board.inputs.search import Found
from lem.board.views import kanban_order, tasks

if TYPE_CHECKING:
    from collections.abc import Iterator

    from lem.board.inputs.text import Look
    from lem.board.views.frame.counted import Counted
    from lem.board.views.world import Seen, World

    # A task with where it stands.
    type Placed = tuple[Seen, kanban_order.Standing]

DONE = "done"


def task_rows(world: World, counts: Counted) -> tuple[Found, ...]:
    """The search's rows of tasks, in their order."""
    columns = (
        open_rows(world, counts, spec) for spec in tasks.COLUMNS if spec.key != DONE
    )
    rest = (parked_rows(world, counts), done_rows(world, counts))
    return tuple(chain(*columns, *rest))


def placed_in(counts: Counted, column: str) -> list[Placed]:
    """The tasks that stand in `column`, in its order."""
    mine = [pair for pair in counts.placed if pair[1].column == column]
    return kanban_order.ordered(column, mine)


def open_rows(world: World, counts: Counted, spec: tasks.Spec) -> tuple[Found, ...]:
    """The rows of one column that has not ended: `COLUMN · STATUS`."""
    rows = []
    for seen, _ in placed_in(counts, spec.key):
        status = seen.record.task.status
        label = f"{spec.title} · {status}"
        rows.append(found(world, seen, label, spec.look))
    return tuple(rows)


def parked_rows(world: World, counts: Counted) -> tuple[Found, ...]:
    """The parked tasks, the one parked longest first."""
    parked = sorted(
        (pair for pair in counts.placed if pair[1].column == "parked"),
        key=lambda pair: pair[1].since,
    )
    return tuple(found(world, seen, "parked", "quiet") for seen, _ in parked)


def done_rows(world: World, counts: Counted) -> Iterator[Found]:
    """Every ended task, the newest first: `STATUS DAY`, on the page's clock."""
    for seen, where in placed_in(counts, DONE):
        day = where.since.astimezone(world.clock.zone).date().isoformat()
        status = seen.record.task.status
        label = f"{status} {day}"
        yield found(world, seen, label, DONE, ended=True)


def found(
    world: World, seen: Seen, chip: str, look: Look, *, ended: bool = False
) -> Found:
    """A task's row, which opens in the panel."""
    slug = seen.record.task.slug
    return Found(
        kind="task",
        key=slug,
        title=title_of(slug),
        chip=chip,
        look=look,
        href=task_href(world.viewer.base, slug, under=world.viewer.view),
        open=not ended,
        frame=True,
    )
