"""The owner's merge refused because the base moved, and his merge standing (`landing.md` D,
"Standing merge", and E, "Owner merge refused for the base"): his word is kept with the
reasons he saw; after a safe read the board's server carries it out; it ends when the reasons
change or a new round's rebase shows no carry, and nothing of his stands for the merge agent."""

from msgspec.structs import replace

from histories.story import TITLE, Story
from lem.kernel.errors import Refusal
from lem.model.criteria import contract
from lem.model.landing import merge, merge_standing, standing
from lem.model.landing.merge_asked import Asked
from lem.records.landing.propose import OwnerMerge
from unit.landing.merges import alone, facing
from unit.landing.proposals import changed
from unit.landing.worlds import CRITERION, TIP, TREE

WORD = Asked(by="owner", via="board", tip=TIP, subject=TITLE)
SERVER = Asked(by="owner", via="server", standing=True, subject=TITLE)
SAFE = "Verdict: merge. One word of the docs.\nBase: safe. Only README.md moved."


def refused_for_the_base() -> Story:
    """A request the owner merges (its criteria approved without him), his word refused
    because origin's base moved, kept with his merge standing."""
    story = Story(record=alone(), world=facing())
    story.base_moved()
    refusal = story.refused(merge.decide(story.record, story.world, WORD, TREE))
    assert refusal.code == "base"
    kept = merge_standing.kept(story.record, refusal, WORD, story.world.now)
    assert kept is not None
    refused, stands = kept
    story.write(refused=refused, standing=stands)
    return story


def test_his_word_refused_for_the_base_stands_and_the_server_merges_after_a_safe_read() -> (
    None
):
    story = refused_for_the_base()
    refused, stands = story.landing.refused, story.landing.standing
    assert refused is not None
    assert stands is not None
    assert (refused.source, refused.kind, refused.by) == ("lem", "base", "owner")
    assert (stands.tip, stands.by_act) == (TIP, "board")
    assert story.due().step == "merge-review"
    story.merge_review(SAFE)
    found = story.due()
    assert (found.step, found.by) == ("merge", "owner")
    assert found.why.startswith(
        "the owner's merge stands: the board's server merges it"
    )
    story.merge(SERVER)
    assert story.calls == [f"merge squash {TIP}"]


def test_his_merge_ends_when_the_reasons_it_is_not_green_change() -> None:
    story = refused_for_the_base()
    story.merge_review(SAFE)
    change = changed(
        5,
        "changed",
        CRITERION.number,
        "the login takes a code.",
        was=CRITERION.text,
        now="The login takes a code.",
    )
    task = story.record.task
    story.record = replace(story.record, task=replace(task, decisions=(change,)))
    assert merge_standing.standing_of(story.record) is None
    found = story.due()
    assert (found.step, found.by) == ("merge", "owner")
    assert not found.why.startswith("the owner's merge stands")
    refused = merge.decide(story.record, story.world, SERVER, TREE)
    assert isinstance(refused, Refusal)
    assert refused.why == (
        f"no merge of the owner's stands for {TIP}: the proposal ended it: nothing was merged"
    )
    assert story.calls == []


def test_a_new_round_whose_rebase_showed_no_carry_ends_his_merge() -> None:
    story = refused_for_the_base()
    landing = story.landing
    digest = merge_standing.digest_of(
        merge_standing.reasons_now(story.record), contract.mark(story.record.task)
    )
    assert standing.standing(landing, digest, carried=True) == OwnerMerge(
        state="stands", why="the change and its reasons stay"
    )
    ended = standing.standing(landing, digest, carried=False)
    assert ended == OwnerMerge(
        state="ended", why="no review covers the change on the new base"
    )


def test_a_refusal_of_the_merge_agent_or_the_server_keeps_no_standing_merge() -> None:
    story = Story(record=alone(), world=facing())
    story.base_moved()
    for asked in (Asked(by="merger", via="server", subject=TITLE), SERVER):
        refusal = merge.decide(story.record, story.world, asked, TREE)
        assert isinstance(refusal, Refusal)
        kept = merge_standing.kept(story.record, refusal, asked, story.world.now)
        assert kept is None or kept[1] is None
