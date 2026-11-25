"""`propose`: the push and the pull request (`landing.md` C, row 7; E, "Push recorded first").

It holds while the proposal names the tip, Lem's last push is the tip, and the forge's head is the
tip. The push is recorded before the forge's call, so a run cut off after it finds the push as
its own; an open pull request on the branch is the task's only when its head is a commit Lem
pushed. A new round's text edit, a closed request and the not-green reasons past the plain ones
are the step `land-propose`'s.
"""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.landing import green, merge
from lem.model.landing.invariants import protected
from lem.model.landing.review import newest
from lem.model.landing.world import Due, Held, PullSeen, World
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


def adopted(record: Record, world: World) -> Refusal | PullSeen | None:
    """The open pull request on the branch that is the task's: one whose head is the commit
    Lem's recorded push sent. Any other open one is somebody else's, and refused
    (`main:land.cmd_propose`)."""
    pushed = (record.landing or Landing()).pushed
    others = [pull for pull in world.candidates if pull.head != pushed]
    if others:
        pull, slug = others[0], record.task.slug
        return Refusal(
            "foreign-pull",
            f"pull request {pull.number} is open on {world.branch} at {pull.head}, a head "
            "Lem did not push: it is somebody else's",
            "give the task a branch of its own (git branch -m NEW-NAME in the worktree), "
            f"then lem land propose {slug} again",
        )
    return world.candidates[0] if world.candidates else None


def decide(record: Record, world: World) -> Refusal | Proposal:
    """What the proposal does, or why it may not be made."""
    guard = protected(world.branch, world.rules, "pushes")
    if guard is not None:
        return guard
    adopt = adopted(record, world)
    if isinstance(adopt, Refusal):
        return adopt
    reasons = green.reasons(record)
    last = newest(record.landing or Landing())
    proposed = Proposed(
        tip=world.tip or "",
        base=world.base,
        green=not reasons,
        reasons=reasons,
        careful=bool(last and last.careful),
        who_acts=merge.who(world, reasons),
        at=world.now,
    )
    return Proposal(push=world.remote != world.tip, adopt=adopt, proposed=proposed)
