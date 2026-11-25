"""`propose`: the push and the pull request (`landing.md` C, row 7; E, "Push recorded first").

It holds while the proposal names the tip, Lem's last push is the tip, and the forge's head is the
tip. The push is recorded before the forge's call, so a run cut off after it finds the push as
its own; an open pull request on the branch is the task's only when its head is a commit Lem
pushed. A new round's text edit, a closed request and the not-green reasons past the plain ones
are the step `land-propose`'s.
"""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.landing import green
from lem.model.landing.invariants import protected
from lem.model.landing.review import newest
from lem.model.landing.world import Due, Held, Merger, PullSeen, World
from lem.records.base import Frozen
from lem.records.landing.propose import Proposed
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.records.record import Record

STEP = "propose"


class Proposal(Frozen, frozen=True, kw_only=True):
    """What `propose` does: push or not, the pull request it adopts or none, and the proposal
    the record keeps (its text's path comes once the text is published)."""

    push: bool
    adopt: PullSeen | None = None
    proposed: Proposed


def holds(record: Record, world: World) -> Held | Due:
    """Whether the forge proposes this tip, as Lem pushed it."""
    landing = record.landing or Landing()
    proposed = landing.proposed
    if proposed is None or proposed.tip != world.tip:
        return Due(step=STEP, why="no pull request proposes this tip")
    pull = world.pull
    if landing.pushed != world.tip or pull is None:
        return Due(step=STEP, why="the tip is not on the forge as Lem pushed it")
    if pull.head != world.tip:
        return Due(step=STEP, why="the pull request's head is not this tip")
    return Held(why=f"pull request {pull.number} proposes this tip")


def ours(landing: Landing, world: World) -> bool:
    """Whether the open pull request on the branch has a head Lem pushed: the tip, or the
    commit of its last push."""
    pull = world.pull
    return pull is not None and pull.head in {world.tip, landing.pushed}


def merger(world: World, reasons: tuple[str, ...]) -> Merger:
    """Who merges: the merge agent for a green request the settings let it merge, else the
    owner."""
    if reasons or world.rules.land == "owner":
        return "owner"
    return "merger"


def taken(record: Record, world: World) -> Refusal | None:
    """Why the pull request on the branch is not the task's to propose: it ended, or its head
    is no commit Lem pushed."""
    slug, pull = record.task.slug, world.pull
    if pull is None:
        return None
    if pull.state != "open":
        return Refusal(
            "closed",
            f"the pull request {pull.url} is {pull.state}",
            f"lem land merged {slug} comes first",
        )
    if ours(record.landing or Landing(), world):
        return None
    return Refusal(
        "foreign-pull",
        f"pull request {pull.number} is open on {world.branch} at {pull.head}, a head "
        "Lem did not push: it is somebody else's",
        "give the task a branch of its own (git branch -m NEW-NAME in the worktree), "
        f"then lem land propose {slug} again",
    )


def decide(record: Record, world: World) -> Refusal | Proposal:
    """What the proposal does, or why it may not be made."""
    guard = protected(world.branch, world.rules, "pushes") or taken(record, world)
    if guard is not None:
        return guard
    reasons = green.reasons(record)
    last = newest(record.landing or Landing())
    proposed = Proposed(
        tip=world.tip or "",
        base=world.base,
        green=not reasons,
        reasons=reasons,
        careful=bool(last and last.careful),
        who_acts=merger(world, reasons),
        at=world.now,
    )
    return Proposal(push=world.remote != world.tip, adopt=world.pull, proposed=proposed)
