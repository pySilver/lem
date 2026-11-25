"""The merge agent's answers and the merge call, told against the model (`landing.md` E, "Two
unusable answers", "No answer", "Stop or lost reply around the merge call", "Forge took the call,
not merged yet", "GitHub refuses", "Stale tap"): two answers that cannot be recorded settle the
read, with no third; an intent on record is replaced by the merge, the queue or GitHub's
refusal, and stays, with the owner asked, while only an open request is visible."""

from msgspec.structs import replace

from histories.story import TITLE, Story
from lem.kernel import clock
from lem.model.landing import merge, reconcile
from lem.model.landing.merge_asked import Asked
from unit.landing.worlds import OTHER, SEEN, TIP

BY_MERGER = Asked(by="merger", via="server", subject=TITLE)


def opened(*, read: bool = True) -> Story:
    """The plain landing open, with its read saying merge or with none yet."""
    story = Story()
    for act in (story.start, story.base, story.checks, story.read, story.file):
        act()
    story.propose()
    if read:
        story.merge_review("Verdict: merge. One word of the docs.")
    return story


def merge_calls(story: Story) -> list[str]:
    """The merge calls that went to the forge."""
    return [call for call in story.calls if call.startswith("merge ")]


def test_two_unusable_answers_call_the_owner_and_no_third_read_is_due() -> None:
    story = opened(read=False)
    assert story.due().step == "merge-review"
    story.merge_review(None)
    first = story.landing.reads[-1]
    assert (first.attempts, first.why, first.no_answer) == (
        1,
        "it ended with no answer",
        True,
    )
    assert story.due().step == "merge-review"
    story.merge_review("Looks fine to me.\nVerdict: merge.")
    second = story.landing.reads[-1]
    assert second.attempts == 2
    assert second.why == (
        "the merge agent twice gave no verdict on its first line; its last answer puts "
        "another line above its verdict, `Verdict: merge.`"
    )
    found = story.due()
    assert (found.step, found.by) == ("merge", "owner")
    assert found.why == f"the owner merges it: {merge.CALLS}"


def test_two_unusable_answers_on_a_moved_base_are_another_round() -> None:
    story = opened(read=False)
    story.base_moved()
    story.merge_review("Verdict: merge.")
    story.merge_review(None)
    last = story.landing.reads[-1]
    assert (last.base_call, last.attempts) == ("another round", 2)
    assert story.due().step == "start"


def test_a_merge_the_forge_took_and_holds_in_its_queue_is_followed_to_its_merge() -> (
    None
):
    story = opened()
    story.merge(BY_MERGER)
    story.effect(pull=replace(SEEN, queued="the merge queue"))
    story.reconcile()
    accepted = story.landing.accepted
    assert accepted is not None
    assert (accepted.tip, accepted.queued) == (TIP, "the merge queue")
    assert story.due().step == "merged"
    waits = reconcile.queued(story.record, story.world)
    assert story.refused(waits).code == "queued"
    story.forge_merged()
    assert story.due().step == "merged"
    assert merge_calls(story) == [f"merge squash {TIP}"]


def test_a_merge_github_refused_is_kept_for_its_tip_and_only_the_owner_s_word_merges() -> (
    None
):
    story = opened()
    story.merge(BY_MERGER)
    story.reconcile(dequeued="a required check failed")
    refused = story.landing.refused
    assert refused is not None
    assert (refused.source, refused.line, refused.tip) == (
        "github",
        "a required check failed",
        TIP,
    )
    found = story.due()
    assert (found.step, found.by) == ("merge", "owner")
    assert found.why.startswith("GitHub refused the merge of this tip")
    again = story.refused(merge.decide(story.record, story.world, BY_MERGER, "e" * 40))
    assert again.code == "github"
    owner = Asked(by="owner", via="board", tip=TIP, subject=TITLE)
    story.merge(owner)
    assert merge_calls(story) == [f"merge squash {TIP}", f"merge squash {TIP}"]


def test_a_stop_with_only_an_open_request_visible_keeps_the_intent_and_asks_the_owner() -> (
    None
):
    story = opened()
    story.merge(BY_MERGER)
    intent = story.landing.intent
    assert intent is not None
    story.reconcile()
    assert story.landing.intent == intent
    assert story.said[-1] == (
        f"a merge call for {TIP} went out at {clock.compact(intent.at)}, and GitHub shows "
        f"{SEEN.url} open: the call may not have reached it, and no new call goes unasked"
    )
    found = story.due()
    assert (found.step, found.why) == ("merge", reconcile.RECONCILED)
    assert merge_calls(story) == [f"merge squash {TIP}"]


def test_a_stale_tap_of_the_owner_merges_nothing() -> None:
    story = opened()
    tap = Asked(by="owner", via="board", tip=OTHER, subject=TITLE)
    refused = story.refused(merge.decide(story.record, story.world, tap, "e" * 40))
    assert refused.code == "tip"
    assert refused.why == (
        f"the owner's merge names {OTHER}, and the proposal is {TIP}: nothing was merged"
    )
    assert merge_calls(story) == []
