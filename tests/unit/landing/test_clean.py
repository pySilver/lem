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
    assert not clean.asks_rebase(world(tip=None, local=None), MERGED, TIP)


def test_a_branch_the_base_holds_goes_and_a_forge_copy_elsewhere_stays() -> None:
    sweep = clean.decide(
        LANDED, world(local=OTHER, local_in_base=True, remote=OTHER), clean.Facts()
    )
    assert sweep == clean.Sweep(worktree=True, branch=True, remote=None)
    assert not clean.asks_rebase(world(local=OTHER, local_in_base=True), MERGED, TIP)
    assert not clean.asks_rebase(world(local=TIP, local_in_base=False), MERGED, TIP)


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
    assert inside.why == (
        f"origin's main does not hold the tip {REBASED} of docs/fix-the-login: the forge merged "
        'a commit made after its tip (its "Update branch"); the branch and the forge\'s copy '
        "stay, and nothing was removed"
    )
    assert not clean.asks_rebase(after, MERGED, OTHER)


def test_a_dirty_worktree_or_a_protected_branch_removes_nothing() -> None:
    dirty = clean.decide(LANDED, world(clean=False), clean.Facts())
    assert isinstance(dirty, Refusal)
    assert dirty.code == "dirty"
    assert (
        dirty.why
        == "the worktree of fix-the-login has changes or files of its own: nothing was removed"
    )
    assert (
        dirty.fix
        == "the owner keeps or removes them, then lem land clean fix-the-login runs again"
    )
    guarded = Rules(base="main", protected=(LANDED.task.branch or "",))
    found = clean.decide(LANDED, world(rules=guarded), clean.Facts())
    assert isinstance(found, Refusal)
    assert found.code == "protected"
    assert found.why.endswith("Lem deletes nothing")


def test_a_dropped_or_answered_tasks_branch_goes_only_when_a_base_holds_it() -> None:
    for status, held in (
        ("dropped", "the dropped task's commits"),
        (
            "answered",
            "the answered task's commits, the test that reproduced its bug among them",
        ),
    ):
        record = task(status)
        kept = clean.decide(record, world(remote=TIP), clean.Facts())
        assert isinstance(kept, clean.Sweep)
        assert (kept.worktree, kept.branch, kept.remote) == (True, False, None)
        assert kept.branch_left == (
            f"docs/fix-the-login holds {held}; git branch -D docs/fix-the-login deletes them"
        )
        held_here = clean.decide(record, world(), clean.Facts(in_local_base=True))
        assert held_here == clean.Sweep(worktree=True, branch=True)
        on_base = clean.decide(record, world(local_in_base=True), clean.Facts())
        assert on_base == clean.Sweep(worktree=True, branch=True)


def test_a_rebase_proof_cannot_override_commits_after_the_merge_head() -> None:
    facts = clean.Facts(after_merged=True, rebased=PROOF)
    branch = world(local=REBASED, tip=REBASED, remote=REBASED)
    found = clean.decide(landed_after_push(), branch, facts)
    assert isinstance(found, Refusal)
    assert found.code == "unmerged"
    assert found.why == (
        f"origin's main does not hold the tip {REBASED} of docs/fix-the-login: the branch has "
        "commits after the head the forge merged; the branch and the forge's copy stay, "
        "and nothing was removed"
    )
    assert found.fix == (
        "git log docs/fix-the-login shows what it holds, and git branch -D docs/fix-the-login "
        "removes it; then lem land clean runs again"
    )


def test_cleanup_waits_for_the_merge_record() -> None:
    found = clean.decide(task("landed"), world(), clean.Facts())
    assert isinstance(found, Refusal)
    assert (found.code, found.why, found.fix) == (
        "unmerged",
        "fix-the-login has no merge on record",
        "lem land next fix-the-login",
    )


def test_cleanup_with_no_branch_has_no_ref_to_delete_or_protect() -> None:
    rules = Rules(base="main", protected=("",))
    record = task("dropped")
    gone = world(branch="", tip=None, local=None, rules=rules)
    assert clean.decide(record, gone, clean.Facts()) == clean.Sweep(
        worktree=False, branch=False
    )


def test_a_divergent_branch_stays_when_the_forge_never_merged_its_tip() -> None:
    found = clean.decide(LANDED, world(local=REBASED, tip=REBASED), clean.Facts())
    assert isinstance(found, Refusal)
    assert found.why.endswith(
        ": the forge did not merge its tip; the branch and the forge's copy stay, "
        "and nothing was removed"
    )
