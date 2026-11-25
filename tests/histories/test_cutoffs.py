"""A step cut off after its effect and before its record, at each step of the plain landing
(`landing.md` E, "Recovery", "Push recorded first", "Stop or lost reply around the merge call"):
the same step is due again, finds its effect in the world, and goes on with no second effect
on the forge. A step whose effect is its record and the files it cites (start, checks, read, a
filing with no item to write) is due again as it was."""

import pytest

from histories.story import REBASED, TITLE, Story
from lem.model.landing import clean, propose
from lem.model.landing.merge_asked import Asked
from unit.landing.merges import MOVED
from unit.landing.worlds import TIP

BY_MERGER = Asked(by="merger", via="server", subject=TITLE)


def prepared(upto: int) -> Story:
    """The plain landing with its first `upto` steps of `preparing` done."""
    story = Story()
    for act in (story.start, story.base, story.checks, story.read, story.file)[:upto]:
        act()
    return story


def opened() -> Story:
    """The plain landing open, its read saying merge."""
    story = prepared(5)
    story.propose()
    story.merge_review("Verdict: merge. One word of the docs.")
    return story


@pytest.mark.parametrize(
    ("upto", "step"), [(0, "start"), (2, "checks"), (3, "read"), (4, "file")]
)
def test_a_step_whose_effect_is_its_record_alone_is_due_again(
    upto: int, step: str
) -> None:
    story = prepared(upto)
    assert story.due().step == step
    assert story.due().step == step


def test_a_rebase_cut_off_before_its_record_is_found_on_the_base_and_recorded() -> None:
    story = prepared(1)
    story.base_moved()
    assert story.due().step == "base"
    story.rebase()
    assert story.due().step == "base"
    based = story.base()
    assert (based.tip, based.base) == (REBASED, MOVED)
    assert story.due().step == "checks"


def test_a_proposal_cut_off_after_its_push_and_request_adopts_both_and_pushes_nothing_again() -> (
    None
):
    story = prepared(5)
    made = story.proposal()
    assert isinstance(made, propose.Proposal)
    story.push(made)
    story.request(made, on_record=False)
    assert story.calls == [f"push {TIP}", "create pull request"]
    assert story.due().step == "propose"
    again = story.proposal()
    assert isinstance(again, propose.Proposal)
    assert again.push is False
    assert again.adopt is not None
    assert again.adopt.head == TIP
    story.push(again)
    story.request(again)
    story.opened(again)
    assert story.calls == [f"push {TIP}", "create pull request", "edit pull request 1"]
    assert story.due().step == "merge-review"


def test_a_merge_call_cut_off_before_its_record_is_reconciled_and_never_called_twice() -> (
    None
):
    story = opened()
    story.merge(BY_MERGER)
    story.forge_merged()
    found = story.due()
    assert (found.step, found.by) == ("merged", None)
    assert found.why == "the forge took the merge, or ended the request"
    story.reconcile()
    merged = story.landing.merged
    assert merged is not None
    assert (merged.by, merged.via, merged.merged_head) == ("merger", "server", TIP)
    assert story.landing.intent is None
    assert story.due().step == "merged"
    assert [call for call in story.calls if call.startswith("merge ")] == [
        f"merge squash {TIP}"
    ]


def test_the_bookkeeping_and_the_cleanup_cut_off_are_due_again() -> None:
    story = opened()
    story.merge(BY_MERGER)
    story.forge_merged()
    story.reconcile()
    assert story.due().step == "merged"
    assert story.due().step == "merged"
    story.merged()
    assert story.due().step == "clean"
    story.effect(tip=None, tree=None, local=None, remote=None)
    assert story.due().step == "clean"
    sweep = story.clean()
    assert sweep == clean.Sweep(worktree=False, branch=False)
    assert story.due().step == "done"
