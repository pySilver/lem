"""The owner's merge refused because the base moved, and his merge standing (`landing.md` D,
"Standing merge", and E, "Owner merge refused for the base"): his word is kept with the
reasons he saw; after a safe read the board's server carries it out; it ends when the reasons
change or a new round's rebase shows no carry, and nothing of his stands for the merge agent."""

from msgspec.structs import replace

from histories.story import TITLE, Story
from lem.app.landing import checks_kept
from lem.app.landing.checks_verdict import Verdict
from lem.kernel.errors import Refusal
from lem.model.criteria import contract
from lem.model.landing import merge, merge_standing, proposal_carry, standing
from lem.model.landing.merge_asked import Asked
from lem.records.landing.propose import OwnerMerge
from unit.landing.merges import alone, facing
from unit.landing.proposals import changed
from unit.landing.test_carry import MUST, NEW, RESOLUTION, RESOLUTION_READ
from unit.landing.worlds import CHECKED, CRITERION, REVIEWED, TIP, TREE

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


def test_his_word_refused_for_the_base_stands_and_the_server_requires_new_checks() -> (
    None
):
    story = refused_for_the_base()
    refused, stands = story.landing.refused, story.landing.standing
    assert refused is not None
    assert stands is not None
    assert (refused.source, refused.kind, refused.by) == ("lem", "base", "owner")
    assert (stands.tip, stands.by_act) == (TIP, "board")
    story.merge_review(SAFE)
    assert story.due().step == "start"
    assert (
        story.refused(merge.decide(story.record, story.world, SERVER, TREE)).code
        == "base"
    )
    assert story.calls == []


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


def test_red_checks_do_not_change_what_an_answered_conflict_review_can_carry() -> None:
    states = []
    for red in (False, True):
        story = refused_for_the_base()
        story.start(conflicting=True)
        story.effect(tip=NEW, tree=TREE, base_in_tip=True)
        resolution = replace(RESOLUTION, base=story.world.base)
        story.write(resolution=resolution)
        run = replace(CHECKED, tip=NEW, base=story.world.base)
        if red:
            failed = Verdict(run=replace(run, outcome="red"))
            story.record = checks_kept.kept(
                story.record, world=story.world, verdict=failed, at=story.world.now
            )
        story.write(checked=run)
        nit = replace(MUST, level="nit", against=None)
        story.write(reviews=(REVIEWED, replace(RESOLUTION_READ, findings=(nit,))))
        before = story.landing.proposed
        assert before is not None
        next_proposal = replace(before, tip=NEW, base=story.world.base)
        proposed, read = proposal_carry.judged(story.record, story.world, next_proposal)
        assert proposed.owner_merge is not None and read is None
        states.append(proposed.owner_merge.state)
    assert states == ["ended", "ended"]
