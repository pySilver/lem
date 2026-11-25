"""`propose`: the push and the pull request (`landing.md` C, row 7; E, "Push recorded first";
`main:land.cmd_propose`).

It holds while the proposal names the tip, Lem's last push is the tip, and the forge's head is
the tip. The push is recorded before the forge's call, so a run cut off after it finds the push
as its own; an open pull request on the branch is the task's only when its head is a commit Lem
pushed, and the one on record is edited in a new round. Before any of it, the request passes the
gates of the build and of its notes, each a refusal that names the way on.
"""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.landing import (
    green,
    merge,
    propose_careful,
    propose_gates,
    propose_lines,
    propose_notes,
)
from lem.model.landing.propose_facts import small
from lem.model.landing.world import Due, Held, PullSeen, World
from lem.records.base import Frozen
from lem.records.landing.propose import Proposed
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.model.landing.propose_facts import Facts
    from lem.records.record import Record

STEP = "propose"


class Proposal(Frozen, frozen=True, kw_only=True):
    """What `propose` does: push or not, the pull request it adopts or edits or none, the
    proposal the record keeps (its text's path comes once the text is published), the
    reasons the request is careful, and the notes by their headings."""

    push: bool
    adopt: PullSeen | None = None
    proposed: Proposed
    careful: tuple[str, ...] = ()
    notes: propose_notes.Notes = propose_notes.Notes()


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
    """The task's pull request: the one on record while it is open, else the open one on
    the branch whose head is the commit Lem's recorded push sent. Any other is somebody
    else's, and refused; a merged or closed one on record is the step `merged`'s."""
    slug, pull = record.task.slug, world.pull
    if pull is not None and pull.state != "open":
        action = "finishes the task" if pull.state == "merged" else "writes it dropped"
        return Refusal(
            "closed",
            f"the pull request {pull.url} is {pull.state}",
            f"lem land merged {slug} {action}, and the branch keeps its commits",
        )
    pushed = (record.landing or Landing()).pushed
    others = [found for found in world.candidates if found.head != pushed]
    if others:
        return Refusal(
            "foreign-pull",
            f"pull request {others[0].number} is open on {world.branch} at "
            f"{others[0].head}, a head Lem did not push: it is somebody else's, and Lem "
            "does not push over it or rewrite its text",
            "the owner closes that pull request on GitHub, or asks its author to, then "
            f"lem land propose {slug} again; the task's branch is on its record, so a "
            "rename in the worktree alone does not give it another",
        )
    if pull is not None:
        return pull
    return world.candidates[0] if world.candidates else None


def written(
    record: Record,
    facts: Facts,
    notes: propose_notes.Notes,
    title: str,
    *,
    careful: bool,
) -> Refusal | None:
    """The first gate of the notes and the title the request does not pass, or None: the
    headings the notes hold, and a finding nobody filed, which reaches the pull request only
    with a bar call and its reason or as an item the tip holds, whoever wrote its line."""
    held = propose_lines.wanted(small=small(record), careful=careful)
    lacking = propose_lines.missing(notes, held, record.task.slug)
    found = propose_lines.bare(notes, small=small(record), in_tip=facts.in_tip)
    if lacking is not None or not found:
        return lacking or propose_gates.titled(title)
    listed = "; ".join(f'"{line}"' for line in found)
    return Refusal(
        "no-bar-call",
        f"{len(found)} line(s) of the notes name a finding with no bar call and no item: "
        f"{listed}",
        "give it a bar call and a reason, or file it: by the bar of rule 6 of the "
        "builder's standing rules, the line ends with `under: REASON` or `cheap: REASON`, "
        "or a builder files it as an item of docs/backlog and the line names the item's "
        "path; then this step runs again",
    )


def made(record: Record, world: World, careful: tuple[str, ...]) -> Proposed:
    """The proposal of the tip now: green or the reasons it is not, and who merges it."""
    reasons = green.reasons(record, careful)
    return Proposed(
        tip=world.tip or "",
        base=world.base,
        green=not reasons,
        reasons=reasons,
        careful=bool(careful),
        who_acts="owner" if careful else merge.who(world, reasons),
        at=world.now,
    )


def decide(
    record: Record, world: World, facts: Facts, title: str
) -> Refusal | Proposal:
    """What the proposal does, or why it may not be made."""
    notes = propose_notes.parsed(facts.notes)
    if isinstance(notes, Refusal):
        return notes
    careful = propose_careful.why(record, facts)
    adopt = (
        propose_gates.gates(record, world, facts, careful=bool(careful))
        or written(record, facts, notes, title, careful=bool(careful))
        or adopted(record, world)
    )
    if isinstance(adopt, Refusal):
        return adopt
    return Proposal(
        push=world.remote != world.tip,
        adopt=adopt,
        proposed=made(record, world, careful),
        careful=careful,
        notes=notes,
    )
