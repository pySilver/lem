"""Carry and coverage over a rebase (`model/landing/carry.py`, `rebased.py`; `landing.md` D),
from the facts `base` gathered: git's merge of the reviewed tip onto the new base against the
new tree, never a record of the rebase."""

from msgspec.structs import replace

from lem.model.landing import carry, rebased
from lem.model.landing.rebased import Clash
from lem.records.landing.propose import OwnerMerge, Standing
from lem.records.landing.record import Landing
from unit.landing.worlds import (
    BASE,
    BASED,
    MOMENT,
    OTHER,
    READ,
    REVIEWED,
    TIP,
    TREE,
    world,
)

NEW = "2" * 40
MOVED = "4" * 40
# A rebase of the reviewed tip `TIP` onto `MOVED` that git's merge showed: the tip `NEW`.
CARRIED = replace(BASED, tip=NEW, base=MOVED, before=TIP, carried=True)
UNSHOWN = replace(BASED, tip=NEW, base=MOVED, before=TIP, unshown_paths=("a.txt",))


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
    assert carry.covers(landing, TIP)
    assert carry.covers(landing, NEW)
    assert not carry.covers(landing, OTHER)
    assert not carry.covers(landing, None)
    assert not carry.covers(replace(landing, based=UNSHOWN), NEW)
    assert not carry.covers(replace(landing, based=replace(CARRIED, before=OTHER)), NEW)
    assert not carry.covers(Landing(based=CARRIED), NEW)


def test_only_a_review_of_the_change_that_someone_answered_covers_it() -> None:
    silent = replace(REVIEWED, attempt=2, tip=OTHER, answered=())
    resolution = replace(REVIEWED, attempt=3, tip=OTHER, of="resolution")
    landing = Landing(reviews=(REVIEWED, silent, resolution))
    assert carry.newest(landing) == REVIEWED
    assert carry.covers(landing, TIP)
    assert not carry.covers(landing, OTHER)


def test_a_real_verdict_of_the_tip_before_carries_onto_the_tip_a_shown_rebase_made() -> (
    None
):
    landing = Landing(reads=(READ,), based=CARRIED)
    now = world(tip=NEW, base=MOVED, base_tree=OTHER)
    found = carry.read_carries(landing, now)
    assert found is not None
    assert (
        found.tip,
        found.base,
        found.base_tree,
        found.verdict,
        found.carried_from,
    ) == (
        NEW,
        MOVED,
        OTHER,
        "merge",
        TIP,
    )
    unusable = replace(READ, verdict=None, no_answer=True)
    assert carry.read_carries(replace(landing, reads=(unusable,)), now) is None
    assert carry.read_carries(replace(landing, based=UNSHOWN), now) is None
    assert carry.read_carries(landing, world(tip=OTHER, base=MOVED)) is None
    assert carry.read_carries(landing, world(tip=NEW, base=BASE)) is None
    other = replace(READ, tip=OTHER)
    assert carry.read_carries(replace(landing, reads=(other,)), now) is None
    assert carry.read_carries(Landing(based=CARRIED), now) is None
    assert carry.read_carries(Landing(reads=(READ,)), now) is None


def test_the_owners_merge_stands_while_the_change_and_its_reasons_stay() -> None:
    standing = Standing(tip=TIP, reasons_digest="d", by_act="owner", at=MOMENT)
    landing = Landing(standing=standing, based=CARRIED)
    assert carry.standing(Landing(), "d", covered=True) is None
    assert carry.standing(landing, "d", covered=True) == OwnerMerge(
        state="stands", why="the change and its reasons stay"
    )
    assert carry.standing(landing, "e", covered=True) == OwnerMerge(
        state="ended", why="the reasons it is not green changed"
    )
    assert carry.standing(landing, "d", covered=False) == OwnerMerge(
        state="ended", why="no review covers the change on the new base"
    )
    unshown = carry.standing(replace(landing, based=UNSHOWN), "d", covered=False)
    assert unshown is not None
    assert unshown.why.startswith("the rebase could not be shown to keep the change")
