"""The cleanup (`model/landing/clean.py`): what goes of a landed task's worktree, branch and
forge copy, a branch rebased after its push, one the forge did not merge, and a dropped or
answered task's (`landing.md` E, the clean rows)."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.landing import clean
from lem.model.landing.world import Rules
from unit.landing.merges import code_of
from unit.landing.worlds import MERGED, OPENED, OTHER, TIP, task, world

if TYPE_CHECKING:
    from lem.records.record import Record

LANDED = task("landed", **{**OPENED, "phase": "merged", "merged": MERGED})
REBASED = "7" * 40
PROOF = clean.Rebased(same=True, base_tip="3" * 40, base_merged="4" * 40)


def landed_after_push() -> Record:
    """The landed task whose last push was the head the forge merged."""
    landing = LANDED.landing
    assert landing is not None
    return replace(LANDED, landing=replace(landing, pushed=TIP))


def test_a_landed_branch_at_the_merged_head_goes_with_the_forges_copy() -> None:
    sweep = clean.decide(LANDED, world(remote=TIP), clean.Facts())
    assert sweep == clean.Sweep(worktree=True, branch=True, remote=TIP)


def test_what_went_already_is_not_removed_twice() -> None:
    gone = clean.decide(LANDED, world(tip=None, local=None), clean.Facts())
    assert gone == clean.Sweep(worktree=False, branch=False)


def test_a_branch_the_base_holds_goes_and_a_forge_copy_elsewhere_stays() -> None:
    sweep = clean.decide(
        LANDED, world(local=OTHER, local_in_base=True, remote=OTHER), clean.Facts()
    )
    assert sweep == clean.Sweep(worktree=True, branch=True, remote=None)


def test_a_branch_rebased_after_its_push_goes_when_it_holds_the_same_change() -> None:
    pushed = landed_after_push()
    facts = clean.Facts(rebased=PROOF)
    rebased = world(local=REBASED, tip=REBASED, remote=TIP)
    assert clean.asks_rebase(rebased, MERGED, TIP)
    sweep = clean.decide(pushed, rebased, facts)
    assert isinstance(sweep, clean.Sweep)
    assert (sweep.branch, sweep.remote) == (True, TIP)
    assert sweep.rebased is not None
    assert "holds the same change as 111111111" in sweep.rebased


def test_a_branch_changed_after_its_push_stays_and_the_forges_copy_goes() -> None:
    pushed = landed_after_push()
    facts = clean.Facts(rebased=replace(PROOF, same=False))
    sweep = clean.decide(pushed, world(local=REBASED, tip=REBASED, remote=TIP), facts)
    assert isinstance(sweep, clean.Sweep)
    assert (sweep.branch, sweep.remote) == (False, TIP)
    assert sweep.branch_left is not None
    assert (
        "`git range-diff 444444444..111111111 333333333..777777777`"
        in sweep.branch_left
    )
    assert f"`git branch -D {LANDED.task.branch}`" in sweep.branch_left


def test_a_tip_the_forge_did_not_merge_keeps_the_branch_and_its_copy() -> None:
    after = world(local=REBASED, tip=REBASED, remote=REBASED)
    found = clean.decide(LANDED, after, clean.Facts(after_merged=True))
    assert code_of(found) == "unmerged"
    assert isinstance(found, Refusal)
    assert "commits after the head the forge merged" in found.why
    inside = clean.decide(LANDED, after, clean.Facts(inside_merged=True))
    assert code_of(inside) == "unmerged"
    assert isinstance(inside, Refusal)
    assert '"Update branch"' in inside.why
    assert not clean.asks_rebase(after, MERGED, OTHER)


def test_a_dirty_worktree_or_a_protected_branch_removes_nothing() -> None:
    assert code_of(clean.decide(LANDED, world(clean=False), clean.Facts())) == "dirty"
    guarded = Rules(base="main", protected=(LANDED.task.branch or "",))
    assert (
        code_of(clean.decide(LANDED, world(rules=guarded), clean.Facts()))
        == "protected"
    )


def test_a_dropped_or_answered_tasks_branch_goes_only_when_a_base_holds_it() -> None:
    for status, held in (
        ("dropped", "the dropped task's commits"),
        ("answered", "reproduced"),
    ):
        record = task(status)
        kept = clean.decide(record, world(remote=TIP), clean.Facts())
        assert isinstance(kept, clean.Sweep)
        assert (kept.worktree, kept.branch, kept.remote) == (True, False, None)
        assert held in (kept.branch_left or "")
        held_here = clean.decide(record, world(), clean.Facts(in_local_base=True))
        assert held_here == clean.Sweep(worktree=True, branch=True)
        on_base = clean.decide(record, world(local_in_base=True), clean.Facts())
        assert on_base == clean.Sweep(worktree=True, branch=True)
