"""`base`: the task's branch on origin's base as it is now (`landing.md` C, row 2; E, "Teammate
commit", "Conflict with the base", "Rebase refused by git", "Merge-only change").

It holds while origin's base is the base the branch was put on and the tip holds it, the tip
has a commit of its own, origin's task branch holds no commit Lem did not push, and no rebase is
in progress. A tip that does not hold origin's base is rebased, the plain rebase a developer
runs; what the rebase kept of the change, and whether the review carries over it, is judged
from git's merge of the tip before it onto the base (`rebased.py`, `carry.py`).
"""

from typing import TYPE_CHECKING, Literal

from lem.model.landing import base_said, rebased
from lem.model.landing.world import Due, Held, World
from lem.records.base import Frozen, Sha
from lem.records.landing.record import Landing
from lem.records.landing.start import Based

if TYPE_CHECKING:
    from lem.kernel.errors import Refusal
    from lem.records.record import Record

STEP = "base"
# What `base` does: nothing but its record, or a rebase onto origin's base.
type Move = Literal["onto", "rebase"]


class Facts(Frozen, frozen=True, kw_only=True):
    """What `base` reads before it acts: the commits of the tip that origin's base lacks, and
    each commit of origin's task branch that a teammate made, as a line."""

    ahead: int
    theirs: tuple[str, ...] = ()


class After(Frozen, frozen=True, kw_only=True):
    """What `base` reads after its move: the tip and its tree, the commits it has that origin's
    base lacks, git's merge of the tip before onto the base (None with no rebase) and the paths
    where the tip's tree differs from it, git's merge of the newest reviewed tip onto the base,
    and the commits the rebase left out."""

    tip: Sha
    tree: Sha
    ahead: int
    merged: rebased.Merged = None
    differ: tuple[str, ...] = ()
    reviewed: rebased.Merged = None
    left_out: tuple[Sha, ...] = ()


def foreign(landing: Landing, world: World) -> bool:
    """Whether origin's task branch holds a commit that neither the tip holds nor Lem pushed:
    a teammate's."""
    return (
        world.remote is not None
        and not world.remote_in_tip
        and world.remote != landing.pushed
    )


def holds(record: Record, world: World) -> Held | Due:
    """Whether the branch is on origin's base as it is now, with a commit of its own."""
    landing = record.landing or Landing()
    based = landing.based
    if world.rebasing:
        return Due(step=STEP, why="a rebase is in progress in the worktree")
    if foreign(landing, world):
        return Due(step=STEP, why="origin's branch has a commit Lem did not push")
    if based is None or based.base != world.base or not world.base_in_tip:
        return Due(step=STEP, why="the branch is not on origin's base as it is now")
    if world.tip == world.base:
        return Due(step=STEP, why="the branch has no commit of its own")
    return Held(why="the branch is on origin's base")


def decide(record: Record, world: World, facts: Facts, where: str) -> Refusal | Move:
    """Whether the branch needs a rebase, or why it may not have one now; `where` is the
    worktree, which a fix names."""
    landing = record.landing or Landing()
    if world.rebasing:
        return base_said.in_progress(record, where)
    if foreign(landing, world):
        return base_said.teammate(record, world, facts.theirs, where)
    if not facts.ahead:
        lost = base_said.lost(record, world, landing.based, where)
        return lost or base_said.nothing(record)
    return "onto" if world.base_in_tip else "rebase"


def judged(world: World, after: After) -> Based:
    """What `base` records of its move: where the tip is, whether the review carried, and what
    the rebase did not show it kept."""
    before = world.tip or after.tip
    merged = after.merged
    paths = () if merged is None else rebased.unshown(merged, after.differ)
    return Based(
        tip=after.tip,
        base=world.base,
        before=before,
        carried=not paths and rebased.carried(after.reviewed, after.tree),
        unshown_paths=paths,
        unshown_commits=after.left_out if paths else (),
        at=world.now,
    )


def emptied(
    record: Record, world: World, based: Based, ahead: int, where: str
) -> Refusal | None:
    """The refusal of a rebase that left the branch no commit of its own: a change that sat
    only in a merge commit, which a rebase drops, or nothing to land."""
    if ahead:
        return None
    return base_said.lost(record, world, based, where) or base_said.nothing(record)
