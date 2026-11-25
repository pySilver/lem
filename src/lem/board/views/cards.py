"""A task's card on its column of Tasks (`board_pages.task_card` on `main`): its title, what was
asked, its line and that line's hover, its time, the bar of its plan, and its chips."""

import re
from typing import TYPE_CHECKING

from lem.board.inputs import clock, names
from lem.board.inputs.tasks import Progress, TaskCard
from lem.board.views import chips, hovers, owed, telling

if TYPE_CHECKING:
    from lem.board.inputs.parts import When
    from lem.board.views.standing import Standing
    from lem.board.views.world import Seen, World

DONE = "done"
JOB = re.compile(r"task (?P<at>\d+) of \d+")


def card(world: World, seen: Seen, where: Standing, title: str) -> TaskCard:
    """A task's card on the column titled `title`."""
    task = seen.record.task
    named = names.title_of(task.slug)
    return TaskCard(
        slug=task.slug,
        title=named,
        href=names.task_href(world.viewer.base, task.slug),
        ask=ask_of(task.ask, named),
        status=task.status,
        look=where.look,
        line=telling.line(seen.record, where, title),
        line_title=hovers.hover(task, not_green(seen)),
        live=where.live and where.column != DONE,
        since=time_of(world, where),
        progress=progress_of(seen, where),
        chips=chips.chips(seen, owed.of_task(world, task.slug)),
        selected=task.slug == world.viewer.task,
    )


def ask_of(ask: str, title: str) -> str | None:
    """What was asked, none when it says what the title says."""
    flat = " ".join(ask.split())
    return None if not flat or flat.lower() == title.lower() else flat


def time_of(world: World, where: Standing) -> When:
    """How long the task is in its place, or how long ago it ended."""
    now, zone = world.clock.now, world.clock.zone
    stamp = clock.stamp(where.since, now, zone)
    if where.column == DONE:
        return clock.gone(where.since, now, f"ended {stamp}")
    return clock.since(where.since, now, f"in this state since {stamp}")


def progress_of(seen: Seen, where: Standing) -> Progress | None:
    """The bar of a task that builds its plan: the task of the plan that runs."""
    task = seen.record.task
    total = task.plan.tasks if task.plan else None
    at = running_task(seen)
    if where.column != "build" or at is None or not total:
        return None
    return Progress(
        at=at,
        of=total,
        title=f"task {at} of {total} of the plan",
        done=round(100 * (at - 1) / total, 3),
        width=round(100 / total, 3),
    )


def running_task(seen: Seen) -> int | None:
    """The number of the plan's task that runs (`task 2 of 3`), or None."""
    jobs = [
        span.job or ""
        for span in seen.record.task.spans
        if span.name == "task" and span.end is None
    ]
    found = JOB.match(jobs[-1]) if jobs else None
    return int(found["at"]) if found else None


def not_green(seen: Seen) -> str | None:
    """`not green` for a task whose proposal is not green, the hover of its line."""
    landing = seen.record.landing
    proposed = landing.proposed if landing else None
    return "not green" if proposed and not proposed.green else None
