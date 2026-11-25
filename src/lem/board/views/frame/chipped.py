"""The chip of a task's row of the search (`board_model.search_rows` on `main`): the column and
the status of a task that did not end, the status and the day of one that ended."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lem.board.views import tasks
    from lem.board.views.standing import Standing
    from lem.board.views.world import Seen, World


def open_chip(spec: tasks.Spec, seen: Seen) -> str:
    """`Waits for you · building`: the column and the task's status."""
    status = seen.record.task.status
    return f"{spec.title} · {status}"


def ended_chip(world: World, seen: Seen, where: Standing) -> str:
    """`landed 2026-11-25`: the status and the day it ended, on the page's clock."""
    day = where.since.astimezone(world.clock.zone).date().isoformat()
    status = seen.record.task.status
    return f"{status} {day}"
