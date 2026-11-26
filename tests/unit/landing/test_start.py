"""`start` (`model/landing/start.py`, `start_said.py`, `begin.py`): a round of the landing
begins from a ready task, goes on with a round a stop or a red base cut, and starts an open
task's new round; what it refuses, by its code; the block of a project with no command of the
checks, and its end (`landing.md` E, "Recovery", "No checks", "Relands")."""

from datetime import timedelta
from typing import TYPE_CHECKING, Literal

import pytest
from inline_snapshot import snapshot
from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.landing import begin, start, start_said
from lem.model.landing.world import Due, Held, Rules
from lem.records.holds import Blocked, Parked
from lem.records.journal.merge import LandAgain
from lem.records.journal.task import StateNoted
from lem.records.landing.merge import Refused
from lem.records.landing.start import Resolution, Started
from unit.landing.worlds import (
    BRANCH,
    MOMENT,
    OPENED,
    PREPARED,
    STARTED,
    TIP,
    task,
    world,
)

if TYPE_CHECKING:
    from lem.records.record import Record

FACTS = start.Facts()
BARE = Rules(base="main")


def code_of(found: object) -> str:
    """The code of a refusal; a case fails on anything else."""
    assert isinstance(found, Refusal), found
    return found.code


def started_of(
    record: Record, *, conflicting: bool = False, **fields: object
) -> Started:
    """The start `decide` gives for `record` in the world of `fields`; a refusal fails."""
    made = start.decide(record, world(**fields), FACTS, conflicting=conflicting)
    assert not isinstance(made, Refusal), made
    return made


def test_a_ready_task_starts_round_one_on_its_branch_and_base() -> None:
    started = started_of(task("ready"))
    assert (started.round, started.branch, started.base_ref, started.conflicting) == (
        1,
        BRANCH,
        "main",
        False,
    )
    later = MOMENT + timedelta(minutes=1)
    started = replace(started, at=later)
    after = begin.begun(task("ready"), started)
    assert (after.task.status, after.task.since) == ("landing", later)
    assert after.landing is not None
    assert after.landing.started == started
    assert after.journal[-1] == StateNoted(
        at=later, status="landing", line="the checks start"
    )


def test_start_refuses_a_status_a_dirty_or_gone_worktree_and_another_branch() -> None:
    status = start.decide(task("building"), world(), FACTS, conflicting=False)
    assert isinstance(status, Refusal)
    assert status.code == "status"
    assert (
        status.fix
        == "lem task move fix-the-login ready, once its builder's change is committed"
    )
    merged = task("ready", **{**OPENED, "phase": "merged"})
    assert code_of(start.decide(merged, world(), FACTS, conflicting=False)) == "status"
    ended = task("ready", **{**OPENED, "phase": "ended"})
    assert code_of(start.decide(ended, world(), FACTS, conflicting=False)) == "status"
    dirty = start.decide(task("ready"), world(clean=False), FACTS, conflicting=False)
    assert isinstance(dirty, Refusal)
    assert (dirty.code, dirty.why, dirty.fix) == (
        "dirty",
        "the task's worktree has changes nobody committed",
        "the builder commits them or removes them, then this step runs again",
    )
    gone = start.decide(task("ready"), world(tip=None), FACTS, conflicting=False)
    assert code_of(gone) == "no-worktree"
    assert isinstance(gone, Refusal)
    assert f"git worktree add .lem/worktrees/fix-the-login {BRANCH}" in gone.fix
    assert gone.why == "the task has no worktree at .lem/worktrees/fix-the-login"
    assert gone.fix == (
        "in the main checkout, `git worktree prune` forgets a worktree whose folder was "
        f"removed by hand, and `git worktree add .lem/worktrees/fix-the-login {BRANCH}` "
        "puts the task's branch back in it; then this step runs again. When the work "
        "is gone with it, `lem task move fix-the-login dropped` ends the task"
    )
    off = start.decide(
        task("ready"), world(), start.Facts(on_branch=False), conflicting=False
    )
    assert code_of(off) == "off-branch"
    assert isinstance(off, Refusal)
    assert (off.why, off.fix) == snapshot(
        (
            "the task's worktree is not on its branch docs/fix-the-login, which the landing pushes and deletes after the merge",
            "`git -C .lem/worktrees/fix-the-login switch docs/fix-the-login` in the main checkout puts it back on it, then this step runs again",
        )
    )


def test_a_protected_task_branch_or_the_base_starts_no_landing() -> None:
    guarded = Rules(base="main", commands=("true",), protected=(BRANCH,))
    found = start.decide(task("ready"), world(rules=guarded), FACTS, conflicting=False)
    assert isinstance(found, Refusal)
    assert found.code == "protected"
    assert found.why.endswith("Lem pushes nothing")
    on_base = start.decide(
        task("ready"), world(branch="main"), FACTS, conflicting=False
    )
    assert code_of(on_base) == "protected"


def test_with_no_command_of_the_checks_start_blocks_the_task_and_then_takes_it_back() -> (
    None
):
    refused = start.decide(task("ready"), world(rules=BARE), FACTS, conflicting=False)
    assert code_of(refused) == "no-checks"
    assert isinstance(refused, Refusal)
    assert (refused.why, refused.fix) == (
        (
            "the project has no command in its checks, so nothing would show that the "
            "change works; the task is blocked"
        ),
        (
            "add the commands to checks.commands in .lem/settings.toml, or, for the task "
            "that sets up the checks, in its own branch's; then lem land start fix-the-login again"
        ),
    )
    blocked = begin.blocked(task("ready"), refused, MOMENT)
    assert blocked.task.hold == Blocked(
        why=start_said.NO_CHECKS, fix=refused.fix, since=MOMENT
    )
    assert blocked.journal == (
        StateNoted(at=MOMENT, status="ready", hold="blocked", line=refused.why),
    )
    assert blocked.task.status == "ready"
    assert begin.blocked(blocked, refused, MOMENT) == blocked
    taken = started_of(blocked)
    assert begin.begun(blocked, taken).task.hold is None


def test_a_branch_that_brings_the_first_checks_can_start() -> None:
    rules = replace(BARE, commands=("make test",), own_checks=True)
    found = start.decide(task("ready"), world(rules=rules), FACTS, conflicting=False)
    assert isinstance(found, Started)


def test_another_hold_keeps_the_task_where_it_is() -> None:
    parked = replace(
        task("ready"), task=replace(task("ready").task, hold=Parked(since=MOMENT))
    )
    found = start.decide(parked, world(), FACTS, conflicting=False)
    assert code_of(found) == "held"
    assert isinstance(found, Refusal)
    assert "parked" in found.why
    red = Blocked(
        why="the base is red", fix="lem land start after repair", since=MOMENT
    )
    blocked = replace(task("ready"), task=replace(task("ready").task, hold=red))
    found = start.decide(blocked, world(), FACTS, conflicting=False)
    assert isinstance(found, Refusal)
    assert (found.code, found.fix) == ("held", "lem land start after repair")


def test_conflicting_is_for_an_open_task() -> None:
    found = start.decide(task("ready"), world(), FACTS, conflicting=True)
    assert code_of(found) == "status"
    assert isinstance(found, Refusal)
    assert "--conflicting is for an open task" in found.why
    assert found.fix == "lem land start fix-the-login, without --conflicting"


def test_an_open_task_starts_a_new_round_counted_and_noted() -> None:
    resolution = Resolution(files=("a.py",), before=TIP, after=TIP, base=TIP)
    record = task("open", **OPENED, resolution=resolution, relands=1)
    started = started_of(record, conflicting=True)
    assert (started.round, started.conflicting) == (2, True)
    after = begin.begun(record, started)
    assert after.landing is not None
    assert (after.landing.round, after.landing.relands, after.landing.phase) == (
        2,
        2,
        "preparing",
    )
    assert after.landing.resolution is None
    assert record.landing is not None
    assert after.landing.reviews == record.landing.reviews
    assert after.landing.proposed == OPENED["proposed"]
    assert after.journal[-2] == LandAgain(
        at=MOMENT, round=2, relands=2, conflicting=True
    )
    line = after.journal[-1]
    assert isinstance(line, StateNoted)
    assert line.line == (
        "the forge calls the pull request conflicting: the branch goes onto the base"
    )
    moved = begin.begun(record, started_of(record))
    last = moved.journal[-1]
    assert isinstance(last, StateNoted)
    assert last.line == "the base moved: the checks run again"


def test_a_round_cut_by_a_stop_or_a_red_base_goes_on_with_its_record_whole() -> None:
    kept = replace(STARTED, round=2, conflicting=True, start_over="a new plan")
    record = task("ready", **{**PREPARED, "started": kept, "round": 2, "relands": 1})
    started = started_of(record)
    assert (started.round, started.conflicting, started.start_over) == (
        2,
        True,
        "a new plan",
    )
    after = begin.begun(record, started)
    assert after.landing is not None
    assert record.landing is not None
    assert replace(after.landing, started=None) == replace(record.landing, started=None)
    assert not [entry for entry in after.journal if isinstance(entry, LandAgain)]


def test_the_start_holds_while_its_round_started_and_the_worktree_lands() -> None:
    assert isinstance(start.holds(task("ready"), world()), Due)
    other = task(**{**PREPARED, "round": 2})
    assert (
        start.holds(other, world()).why == "this round of the landing has not started"
    )
    assert isinstance(start.holds(task(**PREPARED), world(clean=False)), Due)
    assert start.holds(task(**PREPARED), world(rules=BARE)) == Due(
        step="start", why="the settings name no command of the checks"
    )
    assert start.holds(task(**PREPARED), world()) == Held(why="round 1 started")


def test_a_ready_task_with_its_round_started_is_due_to_start_again() -> None:
    back = task("ready", **PREPARED)
    assert start.holds(back, world()).why == (
        "the task came back ready: its landing goes on"
    )


def test_a_rebase_in_progress_is_no_dirty_worktree_for_start() -> None:
    moving = world(clean=False, rebasing=True)
    assert start_said.unready(task("ready"), moving) is None
    assert isinstance(start.holds(task(**PREPARED), moving), Held)


@pytest.mark.parametrize(
    ("source", "kind", "keep"),
    [
        ("lem", "tip", False),
        ("lem", "base", True),
        ("github", "tip", True),
    ],
)
def test_a_new_round_only_clears_lems_refusal_of_the_old_tip(
    source: Literal["lem", "github"], kind: Literal["tip", "base"], *, keep: bool
) -> None:
    refused = Refused(
        tip=TIP,
        source=source,
        kind=kind,
        line="the merge waits",
        by="merger",
        at=MOMENT,
    )
    record = task("open", **OPENED, refused=refused)
    after = begin.begun(record, started_of(record, conflicting=True))
    assert after.landing is not None
    assert after.landing.refused == (refused if keep else None)


def test_a_new_round_has_no_conflict_or_start_over_reason_from_the_old_round() -> None:
    old = replace(
        STARTED, conflicting=True, start_over="the owner asked for a new read"
    )
    record = task("open", **{**OPENED, "started": old})
    next_round = started_of(record)
    assert (next_round.round, next_round.conflicting, next_round.start_over) == (
        2,
        False,
        None,
    )
