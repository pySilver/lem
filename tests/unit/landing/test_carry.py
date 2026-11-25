"""Carry and coverage over a rebase (`model/landing/carry.py`, `rebased.py`, `resolution.py`,
`standing.py`; `landing.md` D), from the facts `base` gathered: git's merge of the reviewed tip
onto the new base against the new tree, never a record of the rebase; each carry anchored on the
tip proposed before, as `land.tip_carry` and `land.moved_carry` on `main` anchor it."""

from datetime import timedelta

from msgspec.structs import replace

from lem.model.landing import carry, rebased, resolution, standing
from lem.model.landing.rebased import Clash
from lem.records.landing.propose import OwnerMerge, Standing
from lem.records.landing.record import Landing
from lem.records.landing.review import Finding
from lem.records.landing.start import Resolution
from unit.landing.worlds import (
    BASE,
    BASED,
    MOMENT,
    OTHER,
    PROPOSED,
    READ,
    REVIEWED,
    TIP,
    TREE,
    world,
)

NEW = "2" * 40
MOVED = "4" * 40
LATER = MOMENT + timedelta(hours=1)
# A rebase of the reviewed and proposed tip `TIP` onto `MOVED` that git's merge showed: the
# tip `NEW`, judged an hour after the review.
CARRIED = replace(BASED, tip=NEW, base=MOVED, before=TIP, carried=True, at=LATER)
MUST = Finding(
    id="r1.2", level="must-fix", where="a.py", title="no", what="it", against="over"
)
UNSHOWN = replace(CARRIED, carried=False, unshown_paths=("a.txt",))
NOW = world(tip=NEW, base=MOVED, base_tree=OTHER)
MOVED_ON = Landing(reviews=(REVIEWED,), reads=(READ,), based=CARRIED, proposed=PROPOSED)


def test_a_rebase_is_shown_only_by_a_clean_merge_with_the_tips_tree() -> None:
    assert rebased.carried(TREE, TREE)
    assert not rebased.carried(OTHER, TREE)
    assert not rebased.carried(Clash(files=("f.txt",)), TREE)
    assert not rebased.carried(None, TREE)
    assert rebased.unshown(TREE, ()) == ()
    assert rebased.unshown(OTHER, ("a.txt", "b.txt")) == ("a.txt", "b.txt")
    assert rebased.unshown(Clash(files=("f.txt",)), ("a.txt",)) == ("f.txt",)
    assert rebased.unshown(Clash(files=()), ()) == ("a path git did not name",)


def test_why_a_rebase_carried_nothing_names_its_paths_and_each_commit_left_out() -> (
    None
):
    assert rebased.why_unshown(None) is None
    assert rebased.why_unshown(CARRIED) is None
    assert rebased.why_unshown(UNSHOWN) == (
        "the rebase could not be shown to keep the change: git's merge of the tip before "
        "it onto 444444444 differs in a.txt"
    )
    left = replace(UNSHOWN, unshown_commits=(OTHER,))
    said = rebased.why_unshown(left)
    assert said is not None
    assert said.endswith(
        "the rebase left out each commit whose patch the base holds: 999999999, and "
        "`git cherry-pick HASH` brings one back if the base took it out again"
    )


def test_the_newest_answered_review_covers_its_tip_and_a_rebase_git_showed() -> None:
    landing = Landing(reviews=(REVIEWED,), based=CARRIED)
    assert carry.covers(landing, world(tip=TIP))
    assert carry.covers(landing, NOW)
    assert carry.source(landing, NOW) == TIP
    assert not carry.covers(landing, world(tip=OTHER, base=MOVED))
    assert not carry.covers(landing, world(tip=None))
    assert not carry.covers(replace(landing, based=UNSHOWN), NOW)
    assert not carry.covers(Landing(based=CARRIED), NOW)


def test_a_base_that_moves_nothing_keeps_the_carry_its_merge_shows() -> None:
    # base ran again on the tip its rebase made: no rebase, the same facts
    again = replace(CARRIED, before=NEW)
    assert carry.covers(Landing(reviews=(REVIEWED,), based=again), NOW)


def test_a_carry_holds_only_on_its_base_its_tip_and_for_the_review_it_judged() -> None:
    landing = Landing(reviews=(REVIEWED,), based=CARRIED)
    assert not carry.covers(landing, world(tip=NEW, base=BASE))
    later = replace(REVIEWED, attempt=2, tip=OTHER, at=LATER + timedelta(minutes=1))
    assert not carry.covers(replace(landing, reviews=(REVIEWED, later)), NOW)


def test_a_review_in_the_same_second_as_base_is_no_source_of_a_carry() -> None:
    # a moment does not tell which came first: the review of another tip in base's second
    same = replace(REVIEWED, attempt=2, tip=OTHER, at=LATER)
    landing = Landing(reviews=(REVIEWED, same), based=CARRIED)
    assert carry.source(landing, NOW) is None
    assert not carry.covers(landing, NOW)
    assert carry.covers(landing, replace(NOW, rebased_review=OTHER))


def test_a_second_clean_rebase_keeps_the_already_carried_proposal() -> None:
    prior = replace(PROPOSED, tip=OTHER)
    based = replace(CARRIED, before=OTHER)
    landing = replace(MOVED_ON, proposed=prior, based=based)
    assert carry.proposed_carries(landing, NOW)
    unshown = replace(based, carried=False, unshown_paths=("a.txt",))
    assert not carry.proposed_carries(replace(landing, based=unshown), NOW)


def test_only_a_review_of_the_change_that_someone_answered_covers_it() -> None:
    silent = replace(REVIEWED, attempt=2, tip=OTHER, answered=())
    resolution_read = replace(REVIEWED, attempt=3, tip=OTHER, of="resolution")
    landing = Landing(reviews=(REVIEWED, silent, resolution_read))
    assert carry.newest(landing) == REVIEWED
    assert carry.covers(landing, world(tip=TIP))
    assert not carry.covers(landing, world(tip=OTHER))


def test_a_real_verdict_of_the_tip_proposed_before_carries_onto_a_shown_rebase() -> (
    None
):
    found = carry.read_carries(MOVED_ON, NOW)
    assert found is not None
    assert (found.tip, found.base, found.base_tree, found.verdict) == (
        NEW,
        MOVED,
        OTHER,
        "merge",
    )
    assert found.carried_from == TIP
    unusable = replace(READ, verdict=None, no_answer=True)
    assert carry.read_carries(replace(MOVED_ON, reads=(unusable,)), NOW) is None
    assert carry.read_carries(replace(MOVED_ON, based=UNSHOWN), NOW) is None
    assert carry.read_carries(MOVED_ON, world(tip=OTHER, base=MOVED)) is None
    assert carry.read_carries(MOVED_ON, world(tip=NEW, base=BASE)) is None
    assert carry.read_carries(replace(MOVED_ON, reads=()), NOW) is None
    assert carry.read_carries(replace(MOVED_ON, proposed=None), NOW) is None


def test_a_read_carries_only_for_the_tip_proposed_before() -> None:
    # the merge agent read OTHER; the tip proposed before and carried is TIP
    other = replace(READ, tip=OTHER)
    assert carry.read_carries(replace(MOVED_ON, reads=(other,)), NOW) is None
    elsewhere = replace(PROPOSED, tip=OTHER)
    assert carry.read_carries(replace(MOVED_ON, proposed=elsewhere), NOW) is None


def test_an_older_verdict_never_stands_in_for_a_newer_unusable_answer() -> None:
    unusable = replace(READ, verdict=None, no_answer=True, attempts=2)
    landing = replace(MOVED_ON, reads=(READ, unusable))
    assert carry.latest(landing) is None
    assert carry.read_carries(landing, NOW) is None


RESOLUTION = Resolution(files=("a.txt",), before=TIP, after=NEW, base=MOVED, read=2)
RESOLUTION_READ = replace(
    REVIEWED, attempt=2, tip=NEW, of="resolution", scope="resolution", findings=()
)
RESOLVED = Landing(
    reviews=(REVIEWED, RESOLUTION_READ),
    reads=(READ,),
    resolution=RESOLUTION,
    proposed=PROPOSED,
)


def test_a_clean_read_of_a_resolution_carries_the_merge_read_and_the_owners_merge() -> (
    None
):
    found = resolution.carries(RESOLVED, NOW, careful=False)
    assert found is not None
    assert (found.tip, found.base, found.verdict, found.carried_from) == (
        NEW,
        MOVED,
        "merge",
        TIP,
    )
    owner = Standing(tip=TIP, reasons_digest="d", by_act="owner", at=MOMENT)
    carried = resolution.tip_carries(RESOLVED, NOW, careful=False)
    assert standing.standing(
        replace(RESOLVED, standing=owner), "d", carried=carried
    ) == (OwnerMerge(state="stands", why="the change and its reasons stay"))


def test_a_resolution_carries_nothing_when_careful_read_badly_or_moved_on() -> None:
    assert resolution.carries(RESOLVED, NOW, careful=True) is None
    assert (
        resolution.carries(RESOLVED, world(tip=OTHER, base=MOVED), careful=False)
        is None
    )
    assert (
        resolution.carries(RESOLVED, world(tip=NEW, base=BASE), careful=False) is None
    )
    finding = replace(RESOLUTION_READ, findings=REVIEWED.findings)
    silent = replace(RESOLUTION_READ, answered=())
    called = replace(RESOLUTION_READ, careful=True)
    for read in (finding, silent, called):
        found = replace(RESOLVED, reviews=(REVIEWED, read))
        assert resolution.carries(found, NOW, careful=False) is None
    unread = replace(RESOLVED, resolution=replace(RESOLUTION, read=None))
    assert resolution.carries(unread, NOW, careful=False) is None
    no_verdict = replace(RESOLVED, reads=(replace(READ, verdict=None, no_answer=True),))
    assert resolution.carries(no_verdict, NOW, careful=False) is None
    must = replace(REVIEWED, findings=(MUST,))
    left = replace(RESOLVED, reviews=(must, RESOLUTION_READ))
    assert resolution.carries(left, NOW, careful=False) is None


def test_a_resolution_carries_no_verdict_across_proposals() -> None:
    # the merge agent said merge for TIP; the conflict met OTHER, which the builder resolved
    crossed = replace(RESOLVED, resolution=replace(RESOLUTION, before=OTHER))
    assert resolution.carries(crossed, NOW, careful=False) is None
    assert not resolution.tip_carries(crossed, NOW, careful=False)


OWNER = Standing(tip=TIP, reasons_digest="d", by_act="owner", at=MOMENT)


def test_the_owners_merge_stands_while_the_change_and_its_reasons_stay() -> None:
    landing = replace(MOVED_ON, standing=OWNER)
    carried = carry.proposed_carries(landing, NOW)
    assert carried
    assert standing.standing(Landing(), "d", carried=True) is None
    assert standing.standing(landing, "d", carried=carried) == OwnerMerge(
        state="stands", why="the change and its reasons stay"
    )
    assert standing.standing(landing, "e", carried=carried) == OwnerMerge(
        state="ended", why="the reasons it is not green changed"
    )
    assert standing.standing(landing, "d", carried=False) == OwnerMerge(
        state="ended", why="no review covers the change on the new base"
    )
    unshown = standing.standing(replace(landing, based=UNSHOWN), "d", carried=False)
    assert unshown is not None
    assert unshown.why.startswith("the rebase could not be shown to keep the change")


def test_the_owners_merge_of_another_tip_never_stands_for_this_one() -> None:
    landing = replace(MOVED_ON, standing=replace(OWNER, tip=OTHER))
    assert standing.standing(landing, "d", carried=True) == OwnerMerge(
        state="ended", why="the change is not the one the owner merged"
    )


def test_the_same_tip_on_a_base_that_went_back_carries_nothing() -> None:
    # the tip proposed before is the tip now, and origin's base went back under it
    landing = replace(MOVED_ON, based=replace(BASED, at=LATER), standing=OWNER)
    assert carry.proposed_carries(landing, world(tip=TIP, base=BASE))
    back = world(tip=TIP, base=OTHER)
    assert not carry.proposed_carries(landing, back)
    assert carry.read_carries(landing, back) is None
    ended = standing.standing(
        landing, "d", carried=carry.proposed_carries(landing, back)
    )
    assert ended is not None
    assert ended.state == "ended"
