"""Whether a task is stuck for want of its session, so that the list says so
(`board_model.session_need` on `main`).

`gone`: the task's phase needs an agent and its newest session is gone from the terminal, two
minutes after that session or the task opened. `deaf`: its session lives and left a wake-up
unanswered. The list skips the row when it cannot tell if the session lives, and for a parked
task. An open task needs its session only while the merge agent reads it, which the session
starts. A queued task needs one once all the tasks it waits for landed or were answered. A landed or
dropped task needs one while its worktree is there, since its cleanup is the session's.
"""

from datetime import timedelta
from typing import TYPE_CHECKING, Literal

from lem.model.owner.looks import Row
from lem.model.owner.merging import merge_wait
from lem.records.holds import Parked

if TYPE_CHECKING:
    from collections.abc import Mapping

    from lem.model.owner.looks import Look, Rows, Stop
    from lem.records.base import Moment
    from lem.records.task import Task

type Need = Literal["gone", "deaf"]

DEAF: Need = "deaf"
# The time a session takes from its open to its agent: a guess (`GRACE_MS` on `main`,
# plan-task-4.md section 2, 2026-11-21).
GRACE = timedelta(minutes=2)
ENDED = frozenset(("landed", "answered", "dropped"))
CLEANED = frozenset(("landed", "dropped"))
DONE = frozenset(("landed", "answered"))


def need(look: Look, tasks: Mapping[str, Task], now: Moment) -> Need | None:
    """What the task lacks of its session now, or None."""
    task, session = look.record.task, look.session
    if session is None or isinstance(task.hold, Parked):
        return None
    if session.live:
        return DEAF if session.unanswered else None
    if not needs_agent(look, tasks):
        return None
    if now - max(began(task), session.since) < GRACE:
        return None
    return "gone"


def began(task: Task) -> Moment:
    """When the task began to need its session: an ended task since it ended, any other
    since it opened."""
    return task.since if task.status in ENDED else task.opened


def needs_agent(look: Look, tasks: Mapping[str, Task]) -> bool:
    """Whether the task's phase needs an agent in its session now."""
    task = look.record.task
    if task.status in ENDED:
        return task.status in CLEANED and look.worktree
    if task.status == "open":
        return merge_wait(look.record) == "reads"
    if task.status == "queued":
        return bool(task.after) and all(
            before is not None and before.status in DONE
            for before in map(tasks.get, task.after)
        )
    return True


def session_rows(look: Look, tasks: Mapping[str, Task], now: Moment) -> Rows:
    """The guard's stop that stands, else the session the task lacks."""
    task, session = look.record.task, look.session
    if look.stop is not None:
        return (stopped_row(task.slug, look.stop),)
    lacks = need(look, tasks, now)
    if lacks is None or session is None:
        return ()
    since = max(began(task), session.since)
    return (lacking_row(task.slug, since, lacks),)


def lacking_row(slug: str, since: Moment, lacks: Need) -> Row:
    """The row of a task that lacks its session: gone, or deaf to a wake-up."""
    prefix = DEAF if lacks == DEAF else "session"
    return Row(
        kind="session",
        key=f"{prefix}:{slug}",
        task=slug,
        since=since,
        deaf=lacks == DEAF,
    )


def stopped_row(slug: str, stop: Stop) -> Row:
    """The row of the guard's stop that stands."""
    return Row(
        kind="stopped",
        key=f"stopped:{slug}",
        task=slug,
        since=stop.at,
        unread=stop.unread,
        restarted=stop.restarted,
    )
