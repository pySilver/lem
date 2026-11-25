"""An open pull request whose base moved after the checks (`landing.md` D, "Safe read on a moved
base", and E, "Base moved, open PR", "Base moved after a safe read", "Relands"): the merge agent
reads what moved; on `safe` the merge goes on that base and its line says so, and a later move
reads again; on `another round` a new round runs the base, the checks and the proposal again,
and edits the request on record."""

from datetime import timedelta

from histories.story import REBASED, TITLE, Story
from lem.kernel.errors import Refusal
from lem.model.landing import carry, merge
from lem.model.landing.merge_asked import Asked
from lem.model.landing.reconcile import Trees
from unit.landing.merges import MOVED, MOVED_TREE
from unit.landing.worlds import BASE, TIP, TREE

BY_MERGER = Asked(by="merger", via="server", subject=TITLE)
SAFE = "Verdict: merge. One word of the docs.\nBase: safe. Only README.md moved."
ROUND = "Verdict: merge. One word.\nBase: another round: the login's API moved."


def opened() -> Story:
    """The plain landing open with its read saying merge, then origin's base moved."""
    story = Story()
    for act in (story.start, story.base, story.checks, story.read, story.file):
        act()
    story.propose()
    story.merge_review("Verdict: merge. One word of the docs.")
    story.base_moved()
    return story


def test_a_safe_read_of_the_moved_base_lets_the_merge_go_on_it_with_its_line() -> None:
    story = opened()
    found = story.due()
    assert found.step == "merge-review"
    assert found.why.startswith("no read of the merge agent covers this tip")
    story.merge_review(SAFE)
    read = story.landing.reads[-1]
    assert (read.base, read.base_tree, read.base_call) == (MOVED, MOVED_TREE, "safe")
    assert (story.due().step, story.due().by) == ("merge", "merger")
    going = merge.decide(story.record, story.world, BY_MERGER, TREE)
    assert not isinstance(going, Refusal)
    assert going.body == (
        "The checks ran on main at bbbbbbbbb; it merged on main at aaaaaaaaa, after the "
        "merge agent's read of what moved: Only README.md moved.\n\nLem task: fix-the-login"
    )
    story.merge(BY_MERGER)
    story.forge_merged()
    story.reconcile(Trees(checks=TREE, parent=MOVED_TREE))
    merged = story.landing.merged
    assert merged is not None
    assert (merged.base_checked, merged.base_merged, merged.uncovered) == (
        BASE,
        MOVED,
        None,
    )
    assert merged.text_updated is False


def test_a_base_that_moved_again_after_the_safe_read_is_read_again() -> None:
    story = opened()
    story.merge_review(SAFE)
    story.effect(base="8" * 40, base_tree="6" * 40)
    refused = story.refused(merge.decide(story.record, story.world, BY_MERGER, TREE))
    assert refused.code == "base"
    assert story.calls[-1] == "create pull request"
    assert story.due().step == "merge-review"


def test_a_merge_on_a_base_nothing_covered_lands_with_the_line_that_says_so() -> None:
    story = opened()
    story.merge_review(SAFE)
    story.merge(BY_MERGER)
    story.forge_merged()
    story.reconcile(Trees(checks=TREE, parent="6" * 40))
    merged = story.landing.merged
    assert merged is not None
    assert merged.uncovered is not None
    assert "which no read of the merge agent covered (its read covered aaaaaaaaa)" in (
        merged.uncovered
    )


def test_another_round_runs_the_round_again_and_edits_the_request_on_record() -> None:
    story = opened()
    story.merge_review(ROUND)
    found = story.due()
    assert found.step == "start"
    assert found.why.endswith("needs another round: a new round")
    story.start()
    assert (story.landing.round, story.landing.relands, story.landing.phase) == (
        2,
        1,
        "preparing",
    )
    assert story.due().step == "base"
    story.effect(now=story.world.now + timedelta(minutes=5))
    based = story.base()
    assert (based.tip, based.base, based.carried) == (REBASED, MOVED, True)
    assert story.due().step == "checks"
    story.checks()
    assert story.due().step == "propose"
    carried = carry.read_carries(story.landing, story.world)
    assert carried is not None
    assert (carried.tip, carried.carried_from, carried.verdict) == (
        REBASED,
        TIP,
        "merge",
    )
    made = story.propose()
    assert made.adopt is not None
    assert story.calls[-2:] == [f"push {REBASED}", "edit pull request 1"]
    assert story.due().step == "merge-review"
    story.write(reads=(*story.landing.reads, carried))
    assert (story.due().step, story.due().by) == ("merge", "merger")


def test_a_new_round_with_a_review_in_the_same_second_as_the_rebase_reads_again() -> (
    None
):
    story = opened()
    story.merge_review(ROUND)
    story.start()
    story.base()
    story.checks()
    found = story.due()
    assert (found.step, found.why) == ("read", "nobody reviewed what changed after it")
    landing = story.landing
    assert landing.based is not None
    assert landing.based.at == landing.reviews[-1].at
