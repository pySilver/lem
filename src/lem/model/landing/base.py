"""`base`: the task's branch on origin's base as it is now (`landing.md` C, row 2).

It holds while origin's base is the base the branch was put on, origin's task branch holds no
commit Lem did not push, and no rebase is in progress. The plain path rebases only when the tip
does not hold origin's base. A conflict's repair, the merge-only change and the carry over a
rebase are the step `land-base`'s.
"""

from typing import TYPE_CHECKING, Literal

from lem.kernel.errors import Refusal
from lem.model.landing.world import Due, Held, World
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.records.record import Record

STEP = "base"
# What `base` does: nothing but its record, or a rebase onto origin's base.
type Move = Literal["onto", "rebase"]


def foreign(landing: Landing, world: World) -> bool:
    """Whether origin's task branch holds a commit that neither the tip holds nor Lem
    pushed: a teammate's."""
    return (
        world.remote is not None
        and not world.remote_in_tip
        and world.remote != landing.pushed
    )


def holds(record: Record, world: World) -> Held | Due:
    """Whether the branch is on origin's base as it is now."""
    landing = record.landing or Landing()
    based = landing.based
    if world.rebasing:
        return Due(step=STEP, why="a rebase is in progress in the worktree")
    if foreign(landing, world):
        return Due(step=STEP, why="origin's branch has a commit Lem did not push")
    if based is None or based.base != world.base:
        return Due(step=STEP, why="the branch is not on origin's base as it is now")
    return Held(why="the branch is on origin's base")


def decide(record: Record, world: World) -> Refusal | Move:
    """Whether the branch needs a rebase, or why it may not have one now."""
    slug = record.task.slug
    landing = record.landing or Landing()
    if world.rebasing:
        return Refusal(
            "rebase-in-progress",
            f"a rebase is in progress in the worktree of {slug}",
            "the builder finishes it (git rebase --continue) or ends it "
            "(git rebase --abort), then lem land base runs again",
        )
    if foreign(landing, world):
        return Refusal(
            "teammate",
            f"origin's {world.branch} is at {world.remote}, a commit Lem did not push",
            f"git pull --rebase origin {world.branch} in the worktree brings it in; "
            f"then lem land start {slug} again, and the checks and a read take it",
        )
    return "onto" if world.base_in_tip else "rebase"
