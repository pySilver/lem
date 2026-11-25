"""`start`: a round of the landing begins (`landing.md` B and C, row 1; E, "Recovery", "No
checks", "Conflicting PR on the forge", "Relands").

It holds while the round has started, the worktree is there and clean, and the settings name a
command of the checks. A `ready` task starts round 1, or goes on with the round on record when a
stop, a red base or a builder's way back cut it (the record is kept whole); an `open` task starts
a new round, counted in `relands`, and with `--conflicting` the forge's call of a conflict
brought it.
"""

from typing import TYPE_CHECKING

from lem.model.landing import destination, start_said
from lem.model.landing.invariants import protected
from lem.model.landing.world import Due, Held, World
from lem.records.base import Frozen
from lem.records.landing.record import Landing
from lem.records.landing.start import Started

if TYPE_CHECKING:
    from lem.kernel.errors import Refusal
    from lem.records.record import Record

STEP = "start"
# The statuses a landing starts from: `landing` only to go on with its round.
STARTS = frozenset(("ready", "landing", "open"))


class Facts(Frozen, frozen=True, kw_only=True):
    """What `start` reads beside the world: whether the worktree's HEAD is the task's branch
    at its tip."""

    on_branch: bool = True


def holds(record: Record, world: World) -> Held | Due:
    """Whether this round's start stands for the world now."""
    landing = record.landing
    started = landing.started if landing else None
    if landing is None or started is None or started.round != landing.round:
        return Due(step=STEP, why="this round of the landing has not started")
    if record.task.status != "landing":
        return Due(step=STEP, why="the task came back ready: its landing goes on")
    refused = start_said.unready(record, world)
    if refused is not None:
        return Due(step=STEP, why=refused.why)
    if not world.rules.commands:
        return Due(step=STEP, why="the settings name no command of the checks")
    return Held(why=f"round {started.round} started")


def round_of(record: Record) -> int:
    """The round this start begins: the next one for an `open` task, else the one on
    record."""
    landing = record.landing or Landing()
    if landing.phase == "open":
        return landing.round + 1
    return landing.round


def entry(record: Record, *, conflicting: bool) -> Refusal | None:
    """Why the task may not start a round now: its status, a hold, a `--conflicting` the
    forge does not call, or a phase past the merge."""
    task = record.task
    landing = record.landing or Landing()
    if task.status not in STARTS or landing.phase in {"merged", "ended"}:
        return start_said.status(record)
    if conflicting and task.status != "open":
        return start_said.not_open(record)
    return start_said.held(record)


def ready(record: Record, world: World, facts: Facts) -> Refusal | None:
    """Why the worktree may not land as it is: gone, with changes nobody committed, off the
    task's branch, on a protected branch, or with no command of the checks."""
    refused = start_said.unready(record, world)
    if refused is not None:
        return refused
    if not facts.on_branch:
        return start_said.off_branch(record, world)
    refused = protected(world.branch, world.rules, "pushes")
    if refused is not None:
        return refused
    if not world.rules.commands:
        return start_said.no_checks(record)
    return None


def decide(
    record: Record, world: World, facts: Facts, *, conflicting: bool
) -> Refusal | Started:
    """The start of this round, or why it may not start."""
    refused = entry(record, conflicting=conflicting) or ready(record, world, facts)
    if refused is not None:
        return refused
    landing = record.landing or Landing()
    kept = landing.started
    again = kept is not None and landing.phase == "preparing"
    return Started(
        round=round_of(record),
        branch=world.branch,
        base_ref=destination.recorded(landing) or world.rules.base,
        conflicting=conflicting or (again and kept is not None and kept.conflicting),
        start_over=kept.start_over if again and kept is not None else None,
        at=world.now,
    )
