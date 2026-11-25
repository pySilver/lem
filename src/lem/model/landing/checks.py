"""`polish` and `checks`: the standard track's polish pass, and the project's commands on the
tip that will be proposed (`landing.md` C, rows 3 and 4).

The checks hold while a passed run covers the tip with the commands as they are now
(`land.gate_holds` on `main`). What a run refuses before its first command and after its last
is decided here from the facts the step gathered; the run itself is `app/landing/checks_run.py`.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.kernel import files
from lem.kernel.errors import Refusal
from lem.model.landing.world import Due, Held, Rules, World
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.records.criteria import Criteria
    from lem.records.landing.start import Polished
    from lem.records.record import Record

STEP = "checks"
POLISH = "polish"
# The characters of a commit that a line for the owner names.
SHORT = 9


def inputs(rules: Rules, plan: str | None = None) -> str:
    """One digest of the commands, serial, setup, source of the commands, and plan path."""
    return files.digest(
        msgspec.json.encode(
            (rules.commands, rules.serial, rules.setup, rules.own_checks, plan)
        )
    )


def polished(record: Record, world: World) -> Held | Due:
    """The polish pass of the standard track: due until one is done for this landing. That
    its last commit is still in the tip is the checks' look before their first command
    (`unpolished`), which gives the pass back when it is not."""
    shape = record.task.shape
    if shape is None or shape.track == "small":
        return Held(why="the fast track has no polish pass")
    done = (record.landing or Landing()).polished
    slug = record.task.slug
    if done is None:
        return Due(
            step=POLISH,
            why=f"{slug} takes the standard track, and no polish pass is on record for "
            f"this landing: `lem land polish {slug}` starts it",
        )
    if done.after is None:
        since = done.before[:SHORT]
        return Due(
            step=POLISH,
            why=f"the polish pass started at {since} and is not done: after its builder, "
            f"`lem land polish {slug} --done` checks what it did",
        )
    after = done.after[:SHORT]
    return Held(why=f"the polish pass is done at {after}")


def holds(record: Record, world: World) -> Held | Due:
    """Whether a passed run covers the tip with the commands as they are now."""
    checked = (record.landing or Landing()).checked
    if checked is None or (
        checked.tip != world.tip and not world.items_from(checked.tip)
    ):
        return Due(step=STEP, why="no run of the checks covers this tip")
    plan = record.task.plan
    plan_path = plan.path if plan else None
    if checked.inputs != inputs(world.rules, plan_path):
        return Due(
            step=STEP,
            why="the check definitions changed since the run: commands, serial, setup "
            "or the plan path",
        )
    if checked.outcome != "passed":
        return Due(step=STEP, why=f"the checks of this tip are {checked.outcome}")
    if checked.criteria_digest != record.task.criteria.digest:
        return Due(
            step=STEP, why="the tests of the criteria changed since the checks ran"
        )
    return Held(why="the checks passed on this tip")


def decide(record: Record, world: World) -> Refusal | None:
    """Why the checks may not start: no command to run (`land.checks_ready` on `main`)."""
    if world.rules.commands:
        return None
    slug = record.task.slug
    return Refusal(
        "no-checks",
        "the checks have no command to run, and checks that ran nothing show nothing: the "
        "project has no command in its checks in the main checkout's .lem/settings.toml",
        f"add the commands to checks.commands there, then run `lem land checks {slug}` "
        "again",
    )


def unpolished(record: Record, *, in_tip: bool) -> Refusal | None:
    """Why the checks may not run for want of the polish pass (`land.polish_missing` on
    `main`): its last commit is not in the tip, so the branch was rewritten after the pass by
    something else than `lem land base`. None on the fast track, and while the pass holds."""
    done = (record.landing or Landing()).polished
    if done is None or done.after is None or in_tip:
        return None
    slug, after = record.task.slug, done.after[:SHORT]
    return Refusal(
        "no-polish",
        f"the tip does not hold the polish pass's last commit ({after}): the "
        "branch was rewritten after the pass by something else than `lem land base`",
        f"the pass runs again: `lem land polish {slug}`, its builder, and `--done`",
    )


def pass_kept(polish: Polished | None, now: str, *, small: bool) -> bool:
    """Whether the checks take the polish pass's run of the criteria's tests in place of their
    own (`land.taken_from_polish` on `main`): the standard track, a pass with commits, its run
    passed, and its five inputs (`records.red.Inputs`, as a digest) the same now."""
    if small or polish is None or polish.after is None or not polish.commits:
        return False
    ran = polish.run
    return ran is not None and ran.outcome == "passed" and ran.inputs == now


def moved(before: Criteria, now: Criteria) -> Refusal | None:
    """Why a run of the criteria's tests is not one to keep: the criteria, their tests among
    them, changed since it began (`land.checks_body` on `main` read them again after the
    commands). The contract's own mark (`model/criteria/contract.py`) takes this place once the
    step `criteria` joins."""
    if (before.digest, before.criteria, before.approvals) == (
        now.digest,
        now.criteria,
        now.approvals,
    ):
        return None
    return Refusal(
        "contract-moved",
        "the criteria changed while the checks ran, so their run is not one of the criteria "
        "of now",
        "the checks run again on the criteria of now: lem land next names the step",
    )
