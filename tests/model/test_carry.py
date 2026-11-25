"""Carry and coverage over drawn landings and worlds (`model/landing/carry.py`, `resolution.py`,
`standing.py`, `review*.py`, `merge_evidence.py`; `landing.md` D): a must-fix outlives any
carry, a read with no real verdict never carries, a safe read covers a base only by its tree, a
review covers only its tip or the tip a shown rebase made of it, and a careful request carries
nothing over a resolved conflict."""

from typing import TYPE_CHECKING

from hypothesis import given
from hypothesis import strategies as st
from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.landing import (
    carry,
    green,
    merge_evidence,
    mergeread,
    resolution,
    review,
    review_cover,
    review_due,
    standing,
)
from lem.model.landing.world import Held
from lem.records.landing.record import Landing
from lem.records.landing.start import Resolution
from model.landings import (
    LANDING,
    TREES,
    any_records,
    any_worlds,
    landings,
    moved_landings,
    moved_worlds,
    must_fixed,
    opened_landings,
    worlds,
)
from unit.landing import worlds as plain

if TYPE_CHECKING:
    from lem.model.landing.world import World
    from lem.records.landing.review import Reviewed
    from lem.records.record import Record

# A tree that no read and no run of the checks names.
UNREAD_TREE = "7" * 40


def must_fix(found: Reviewed | None) -> bool:
    """Whether a review left a must-fix."""
    return found is not None and review.must_fix(found) > 0


@LANDING
@given(must_fixed() | any_records(), any_worlds())
def test_a_must_fix_the_newest_review_left_outlives_any_carry(
    record: Record, world: World
) -> None:
    landing = record.landing or Landing()
    last = review.newest(landing)
    if not must_fix(last):
        return
    assert last is not None
    left = review.unmet(record, last, world)
    assert left[0] == f"the last one left {review.must_fix(last)} must-fix"
    assert green.review(landing)
    assert review_due.resolution_due(landing, world) is None
    held = review.holds(record, world)
    if isinstance(held, Held):
        assert held.why.startswith("two rounds reviewed it") or review_cover.QUIET in (
            held.why
        )


@LANDING
@given(record=must_fixed() | any_records(), world=moved_worlds(), careful=st.booleans())
def test_a_must_fix_of_the_review_before_a_resolution_carries_no_read(
    record: Record, world: World, *, careful: bool
) -> None:
    landing = record.landing or Landing()
    if must_fix(carry.newest(landing)):
        assert not resolution.tip_carries(landing, world, careful=careful)
        assert resolution.carries(landing, world, careful=careful) is None


@LANDING
@given(landings("open") | moved_landings(), moved_worlds())
def test_a_careful_request_carries_no_read_over_a_resolved_conflict(
    landing: Landing, world: World
) -> None:
    assert resolution.carries(landing, world, careful=True) is None


@LANDING
@given(
    landing=landings("open") | moved_landings(),
    world=moved_worlds(),
    careful=st.booleans(),
)
def test_a_read_with_no_real_verdict_never_carries(
    landing: Landing, world: World, *, careful: bool
) -> None:
    proposed = landing.proposed
    of_tip = [read for read in landing.reads if proposed and read.tip == proposed.tip]
    if of_tip and (of_tip[-1].verdict is None or of_tip[-1].no_answer):
        assert carry.latest(landing) is None
        assert carry.read_carries(landing, world) is None
        assert resolution.carries(landing, world, careful=careful) is None


@LANDING
@given(
    landing=landings("open") | moved_landings(),
    world=moved_worlds(),
    careful=st.booleans(),
)
def test_a_carried_read_is_the_real_verdict_on_the_tip_and_base_now(
    landing: Landing, world: World, *, careful: bool
) -> None:
    for carried in (
        carry.read_carries(landing, world),
        resolution.carries(landing, world, careful=careful),
    ):
        if carried is None:
            continue
        assert landing.proposed is not None
        assert carried.verdict in {"merge", "call"}
        assert carried.carried_from == landing.proposed.tip
        assert (carried.base, carried.base_tree) == (world.base, world.base_tree)
        assert carried.tip == (world.tip or landing.proposed.tip)


@LANDING
@given(landings("preparing") | moved_landings(), moved_worlds())
def test_a_review_covers_its_own_tip_or_the_tip_a_shown_rebase_made_of_it(
    landing: Landing, world: World
) -> None:
    if not carry.covers(landing, world):
        return
    last, based = carry.newest(landing), landing.based
    assert last is not None
    if last.tip == world.tip:
        return
    assert based is not None
    assert based.carried
    assert (based.tip, based.base) == (world.tip, world.base)
    assert last.at < based.at


@LANDING
@given(opened_landings(), worlds(), st.sampled_from(TREES))
def test_a_safe_read_covers_a_moved_base_only_while_its_tree_is_the_read_one(
    record: Record, world: World, checks_tree: str
) -> None:
    landing = record.landing or Landing()
    refused = merge_evidence.base_side(record, world, checks_tree)
    if refused is None:
        read = mergeread.latest(landing, world.base_tree)
        moved = world.base_tree != checks_tree
        assert not moved or (read is not None and read.base_call == "safe")
        assert read is None or read.base_tree == world.base_tree
    unread = merge_evidence.base_side(
        record, replace(world, base_tree=UNREAD_TREE), checks_tree
    )
    assert isinstance(unread, Refusal)
    assert unread.code in {"base", "protected"}


@LANDING
@given(landings("open"), st.sampled_from(("a", "b")))
def test_a_standing_merge_never_stands_over_a_change_nobody_showed_carried(
    landing: Landing, digest: str
) -> None:
    found = standing.standing(landing, digest, carried=False)
    assert found is None or found.state == "ended"
    stands = standing.standing(landing, digest, carried=True)
    if stands is not None and stands.state == "stands":
        assert landing.standing is not None
        assert landing.proposed is not None
        assert landing.standing.tip == landing.proposed.tip
        assert landing.standing.reasons_digest == digest


def test_with_no_proposal_nothing_carries_and_two_silent_reads_of_a_resolution_go_on() -> (
    None
):
    assert not carry.proposed_carries(Landing(), plain.world())
    before = replace(plain.REVIEWED, tip=plain.OTHER)
    silent = replace(plain.REVIEWED, attempt=2, answered=(), of="resolution")
    waiting = Resolution(
        files=("a.py",), before=plain.OTHER, after=plain.TIP, base=plain.BASE
    )
    landing = Landing(reviews=(before, silent, replace(silent, attempt=3)))
    record = plain.task(
        **{**plain.PREPARED, "reviews": landing.reviews, "resolution": waiting}
    )
    found = review.holds(record, plain.world())
    assert found == Held(
        why=f"{review_cover.QUIET}: the read of a conflict's resolution"
    )
