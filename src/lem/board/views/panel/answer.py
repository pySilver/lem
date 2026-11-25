"""Where the owner answers what waits for him in a task (`board_model.answer_of` on `main`): in
the task's own session or on the board; for a task queued after a dropped one, in any Lem session;
for a task two releases back, the stop's message.

The words of each wait of his own hold are `held.py`'s.
"""

from typing import TYPE_CHECKING

from lem.board.views.panel import held
from lem.board.views.rule import ENDED
from lem.records.holds import Blocked, BreakerHold, OwnerHold, ReleaseHold

if TYPE_CHECKING:
    from lem.records.task import Task

MERGE = "Merge the pull request on GitHub or on this board."
PLAN = (
    "Read the plan, then build it or drop the task on this board, "
    "or tell the task’s session."
)


def answer(task: Task, after: str | None = None) -> str:
    """Where the owner answers the task; `after` names the dropped task it was queued
    behind."""
    hold = task.hold
    if isinstance(hold, ReleaseHold) and task.status not in ENDED:
        return hold.say
    if after is not None:
        return dropped(task.slug, after)
    if isinstance(hold, BreakerHold):
        return breaker(task.slug)
    return going(task)


def going(task: Task) -> str:
    """Where he answers a task no stop, drop or breaker holds: the merge, his own wait, the
    plan, his block, or the task's session."""
    hold = task.hold
    if task.status == "open":
        return MERGE
    if isinstance(hold, OwnerHold):
        return PLAN if hold.on == "plan" else held.answer(task, hold)
    if task.status == "planned":
        return PLAN
    if isinstance(hold, Blocked) and hold.after is None:
        return blocked(task.slug, hold.why)
    return (
        f"Tell the task’s session to build it, or type /lem drop {task.slug} to end it."
    )


def dropped(slug: str, after: str) -> str:
    """Where he answers a task queued after the dropped task `after`: in any Lem session."""
    start, drop = f"start {slug} now", f"/lem drop {slug}"
    return (
        f"It waited for {after}, which was dropped, so the result it "
        f"waited for never came. Type “{start}” to start it without that result, "
        f"or {drop} to end it, in any Lem session of this repository."
    )


def breaker(slug: str) -> str:
    """Where he answers a breaker."""
    return (
        "Read its document, first on the task’s Overview. Then help, park or drop "
        "the task on this board, or help in the task’s session. Or type /lem park "
        f"{slug} to put the task aside, or /lem drop {slug} to end it."
    )


def blocked(slug: str, why: str) -> str:
    """Where he answers a task its session stopped with something it cannot settle alone:
    in that session, which waits for his word."""
    return (
        "The task’s session stopped on something it cannot settle alone: "
        f"“{why}”. Tell it what to do in the task’s session, or "
        f"type /lem drop {slug} there to end the task."
    )
