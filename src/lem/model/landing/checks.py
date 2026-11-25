"""`polish` and `checks`: the standard track's polish pass, and the project's commands on the
tip that will be proposed (`landing.md` C, rows 3 and 4).

The checks hold while a passed run covers the tip with the commands as they are now. The plain
path runs `checks.commands` once, in order; the load gate, `checks.serial`, the removal of what
the commands wrote, the criteria's check and the bar are the step `land-checks`'s.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.kernel import files
from lem.model.landing.world import Due, Held, Rules, World, later
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.kernel.errors import Refusal
    from lem.records.landing.checks import Checked
    from lem.records.record import Record

STEP = "checks"


def inputs(rules: Rules) -> str:
    """One digest of what the checks run: the commands and the serial ones."""
    return files.digest(msgspec.json.encode((rules.commands, rules.serial)))


def polished(record: Record, world: World) -> Held | Due:
    """The polish pass of the standard track; the fast track has none."""
    shape = record.task.shape
    if shape is None or shape.track == "small":
        return Held(why="the fast track has no polish pass")
    return Due(step="polish", why="the standard track's polish pass comes first")


def holds(record: Record, world: World) -> Held | Due:
    """Whether a passed run covers the tip with the commands as they are now."""
    checked = (record.landing or Landing()).checked
    if checked is None or checked.tip != world.tip:
        return Due(step=STEP, why="no run of the checks covers this tip")
    if checked.inputs != inputs(world.rules):
        return Due(step=STEP, why="the checks' commands changed since they ran")
    if checked.outcome != "passed":
        return Due(step=STEP, why=f"the checks of this tip are {checked.outcome}")
    return Held(why="the checks passed on this tip")


def red(checked: Checked | None, world: World) -> bool:
    """Whether the last run covers this tip with these commands, and failed."""
    return (
        checked is not None
        and checked.tip == world.tip
        and checked.inputs == inputs(world.rules)
        and checked.outcome != "passed"
    )


def decide(record: Record, world: World) -> Refusal | None:
    """Why the checks may not run now, or None when they run."""
    checked = (record.landing or Landing()).checked
    if world.rules.serial:
        return later("checks.serial, under the repository's one lock", "land-checks")
    if red(checked, world):
        return later(
            f"the repair of red checks on {world.tip} (a builder's brief, a red base)",
            "land-checks",
        )
    return None


def left(*, clean: bool) -> Refusal | None:
    """Why a run that left the worktree not clean is not one to record."""
    if clean:
        return None
    return later("the removal of what the checks wrote in the worktree", "land-checks")
