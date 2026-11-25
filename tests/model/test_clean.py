"""The cleanup over drawn tasks, worlds and git's facts (`model/landing/clean.py`; `landing.md`
E, the clean rows, and H 3 and 4): nothing goes from a protected branch or a worktree with
changes; the forge's copy goes only at the head the forge merged; a branch goes only when a base
holds its tip, it is the merged head, or a rebase after Lem's push kept that head's change; and a
dropped or answered task's branch with commits of its own stays, with the command that removes
it."""

from typing import TYPE_CHECKING

from hypothesis import given
from hypothesis import strategies as st

from lem.kernel.errors import Refusal
from lem.model.landing import clean
from lem.records.landing.record import Landing
from model.landings import LANDING, any_records, any_worlds, shas
from unit.landing import worlds as plain

if TYPE_CHECKING:
    from lem.model.landing.world import World
    from lem.records.record import Record

FACTS = st.builds(
    clean.Facts,
    in_local_base=st.booleans(),
    after_merged=st.booleans(),
    inside_merged=st.booleans(),
    rebased=st.none()
    | st.builds(clean.Rebased, same=st.booleans(), base_tip=shas(), base_merged=shas()),
)


@LANDING
@given(any_records(), any_worlds(), FACTS)
def test_nothing_goes_from_a_protected_branch_or_a_worktree_with_changes(
    record: Record, world: World, facts: clean.Facts
) -> None:
    found = clean.decide(record, world, facts)
    guarded = world.branch in {world.rules.base, *world.rules.protected}
    dirty = world.tip is not None and not world.clean
    if guarded or dirty:
        assert isinstance(found, Refusal)
        assert found.code == ("protected" if guarded else "dirty")
    elif (
        record.task.status == "landed" and (record.landing or Landing()).merged is None
    ):
        assert isinstance(found, Refusal)
        assert found.code == "unmerged"


def test_a_landed_task_with_no_merge_on_record_removes_nothing() -> None:
    record = plain.task("landed", **{**plain.OPENED, "phase": "merged"})
    found = clean.decide(record, plain.world(), clean.Facts())
    assert isinstance(found, Refusal)
    assert (found.code, found.fix) == ("unmerged", "lem land next fix-the-login")


@LANDING
@given(any_records(), any_worlds(), FACTS)
def test_a_branch_goes_only_when_its_commits_are_landed_or_held_by_a_base(
    record: Record, world: World, facts: clean.Facts
) -> None:
    found = clean.decide(record, world, facts)
    if isinstance(found, Refusal):
        return
    landing = record.landing or Landing()
    assert found.worktree == (world.tip is not None)
    if record.task.status != "landed":
        assert found.remote is None
        if found.branch:
            assert world.local is None or world.local_in_base or facts.in_local_base
        else:
            assert found.branch_left is None or "git branch -D" in found.branch_left
        return
    merged = landing.merged
    assert merged is not None
    assert found.remote in {None, merged.merged_head}
    if found.remote is not None:
        assert world.remote == merged.merged_head
    if found.branch and world.local is not None and not world.local_in_base:
        rebased = facts.rebased
        assert world.local == merged.merged_head or (
            rebased is not None
            and rebased.same
            and landing.pushed == merged.merged_head
        )
    if found.branch_left is not None:
        assert not found.branch
        assert "git branch -D" in found.branch_left
