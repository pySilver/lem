"""The plain fast-track landing, from `ready` to `landed` and `ended`, against the model: the due
step at each point, the record after each step, the forge's calls and the owner's lines
(`landing.md` B and C; the design's part 8, `histories`)."""

from msgspec.structs import replace

from histories.story import TITLE, Story
from lem.kernel.errors import Refusal
from lem.model.landing import propose
from lem.model.landing.merge_asked import Asked
from lem.model.landing.world import Held
from unit.landing.worlds import OTHER, SEEN, TIP

BY_MERGER = Asked(by="merger", via="server", subject=TITLE)


def test_a_fast_task_lands_from_ready_through_each_step_to_its_end() -> None:
    story = Story()
    steps: list[str] = []
    for act in (
        story.start,
        story.base,
        story.checks,
        story.read,
        story.file,
        story.propose,
    ):
        steps.append(story.due().step)
        act()
    assert steps == ["start", "base", "checks", "read", "file", "propose"]
    assert (story.record.task.status, story.landing.phase) == ("open", "open")
    proposed = story.landing.proposed
    assert proposed is not None
    assert (proposed.tip, proposed.green, proposed.who_acts) == (TIP, True, "merger")
    assert story.landing.pushed == TIP
    assert story.calls == [f"push {TIP}", "create pull request"]
    assert story.due().step == "merge-review"
    story.merge_review("Verdict: merge. One word of the docs.")
    found = story.due()
    assert (found.step, found.by) == ("merge", "merger")
    story.merge(BY_MERGER)
    assert story.calls[-1] == f"merge squash {TIP}"
    story.forge_merged()
    assert story.due().step == "merge"
    story.reconcile()
    assert (story.landing.phase, story.record.task.status) == ("merged", "open")
    assert story.due().step == "merged"
    story.merged()
    assert story.due().step == "clean"
    story.effect(remote=TIP)
    sweep = story.clean()
    assert (sweep.worktree, sweep.branch, sweep.remote) == (True, True, TIP)
    assert story.calls[-1] == f"delete docs/fix-the-login at {TIP}"
    assert story.due().step == "done"
    assert story.said[-1] == "the landing ended"


def test_a_notes_line_that_names_a_finding_with_no_bar_call_stops_the_proposal_once() -> (
    None
):
    story = Story()
    for act in (story.start, story.base, story.checks, story.read, story.file):
        act()
    bare = story.proposal("- `a.py`: the login drops a line\n")
    refusal = story.refused(bare)
    assert refusal.code == "no-bar-call"
    assert '"- `a.py`: the login drops a line"' in refusal.why
    assert story.calls == []
    called = story.proposal("- `a.py`: the login drops a line; under: one reader\n")
    assert isinstance(called, propose.Proposal)
    assert not isinstance(called, Refusal)


def test_propose_holds_only_while_the_forge_has_the_tip_as_lem_pushed_it() -> None:
    story = Story()
    for act in (story.start, story.base, story.checks, story.read, story.file):
        act()
    made = story.proposal()
    assert isinstance(made, propose.Proposal)
    story.write(proposed=made.proposed)
    assert story.due().why == "the tip is not on the forge as Lem pushed it"
    story.push(made)
    assert story.due().why == "the tip is not on the forge as Lem pushed it"
    story.request(made)
    story.effect(pull=replace(SEEN, head=OTHER))
    assert story.due().why == "the pull request's head is not this tip"
    story.request(made)
    assert propose.holds(story.record, story.world) == Held(
        why="pull request 1 proposes this tip"
    )
