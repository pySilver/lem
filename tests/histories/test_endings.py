"""How a landing ends without a merge, and the cleanup of each end (`landing.md` B and E,
"Closed on GitHub", "Clean, dropped or answered", "Clean, dirty", "Drop during a step"; H 6): a
request closed on the forge drops the task; a dropped or answered task's worktree goes, its
branch only when a base holds its tip; no step but the cleanup is due after the end."""

import pytest
from msgspec.structs import replace

from histories.story import Story
from lem.model.landing import clean, invariants, start
from lem.model.landing.merge_asked import Asked
from unit.landing.worlds import SEEN, TIP

ENDS_AFTER = ("merge-review", "merge", "start", "base", "checks", "read", "propose")


def opened() -> Story:
    """The plain landing open, its read saying merge."""
    story = Story()
    for act in (story.start, story.base, story.checks, story.read, story.file):
        act()
    story.propose()
    story.merge_review("Verdict: merge. One word of the docs.")
    return story


def test_a_request_closed_on_the_forge_drops_the_task_and_its_cleanup_keeps_his_commits() -> (
    None
):
    story = opened()
    story.effect(pull=replace(SEEN, state="closed"))
    found = story.due()
    assert (found.step, found.why) == (
        "merged",
        "the forge took the merge, or ended the request",
    )
    story.moved("dropped")
    assert story.due().step == "clean"
    for step in ENDS_AFTER:
        refused = invariants.ended("fix-the-login", "dropped", step)
        assert refused is not None
        assert refused.code == "status"
    sweep = story.clean()
    assert sweep.remote is None
    assert (sweep.worktree, sweep.branch) == (True, False)
    assert sweep.branch_left == (
        "docs/fix-the-login holds the dropped task's commits; "
        "git branch -D docs/fix-the-login deletes them"
    )
    assert story.calls == [f"push {TIP}", "create pull request"]
    assert story.due().step == "done"


@pytest.mark.parametrize(
    ("status", "held"),
    [
        ("dropped", "the dropped task's commits"),
        ("answered", "the answered task's commits, the test that reproduced its bug"),
    ],
)
def test_a_task_that_ended_before_its_request_loses_only_its_worktree(
    status: str, held: str
) -> None:
    story = Story()
    story.start()
    story.base()
    story.moved(status)
    assert story.due().step == "clean"
    refused = story.refused(
        start.decide(story.record, story.world, start.Facts(), conflicting=False)
    )
    assert (refused.code, refused.why) == (
        "status",
        (
            f"fix-the-login is {status}: only a ready task, or an open one whose base "
            "moved, starts a landing"
        ),
    )
    story.effect(clean=False)
    dirty = story.refused(clean.decide(story.record, story.world, clean.Facts()))
    assert dirty.code == "dirty"
    story.effect(clean=True)
    sweep = story.clean()
    assert sweep.branch_left is not None
    assert held in sweep.branch_left
    assert story.due().step == "done"


def test_a_dropped_task_whose_branch_a_base_holds_loses_its_branch_too() -> None:
    story = Story()
    story.start()
    story.moved("dropped")
    sweep = story.clean(clean.Facts(in_local_base=True))
    assert (sweep.worktree, sweep.branch, sweep.branch_left) == (True, True, None)


def test_after_the_merge_only_the_bookkeeping_and_the_cleanup_run() -> None:
    story = opened()
    story.merge(Asked(by="merger", via="server", subject="docs: the login works"))
    story.forge_merged()
    story.reconcile()
    story.merged()
    for step in ENDS_AFTER:
        refused = invariants.ended("fix-the-login", "landed", step)
        assert refused is not None
        assert refused.why == (
            "fix-the-login is landed: it ended, and only its cleanup runs now"
        )
    for step in invariants.AFTER_END:
        assert invariants.ended("fix-the-login", "landed", step) is None
    assert story.due().step == "clean"
