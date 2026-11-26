"""Each start of the merge agent, and the reply that counts from one alone: a reply of a start
that a later one of the same tip and base took the place of, or of an earlier round, records
nothing."""

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.landing import dispatches
from lem.records.landing.propose import MergeDispatch
from lem.records.landing.record import Landing
from unit.landing.worlds import BASE, MOMENT, OPENED, OTHER, TIP, task

PRIMARY = "codex/gpt-6.2-sol:high"
FALLBACK = "claude/opus:high"
FIRST = MergeDispatch(
    number=1,
    tip=TIP,
    base=BASE,
    round=1,
    seat=PRIMARY,
    brief="merge-brief-111111111111-bbbbbbbbbbbb-1-1.md",
    at=MOMENT,
)


def held(*started: MergeDispatch, round_number: int = 1) -> Landing:
    landing = task("open", **OPENED).landing or Landing()
    return replace(landing, round=round_number, dispatches=started)


def resolved(landing: Landing, number: int | None, base: str = BASE) -> object:
    record = replace(task("open", **OPENED), landing=landing)
    pinned = dispatches.Pinned(tip=TIP, base=base, dispatch=number)
    return dispatches.resolved(record, pinned)


def code_of(found: object) -> str:
    assert isinstance(found, Refusal), found
    return found.code


def test_a_start_on_the_same_seat_repeats_the_dispatch_and_another_seat_does_not() -> (
    None
):
    landing = held(FIRST)
    assert dispatches.repeated(landing, TIP, BASE, PRIMARY) == FIRST
    assert dispatches.repeated(landing, TIP, BASE, FALLBACK) is None
    assert dispatches.repeated(landing, TIP, OTHER, PRIMARY) is None
    assert dispatches.repeated(held(FIRST, round_number=2), TIP, BASE, PRIMARY) is None
    again = dispatches.started(landing, (TIP, BASE, PRIMARY), MOMENT)
    assert again == FIRST
    stood = dispatches.started(landing, (TIP, BASE, FALLBACK), MOMENT)
    assert (stood.number, stood.seat, stood.round) == (2, FALLBACK, 1)
    assert stood.brief == "merge-brief-111111111111-bbbbbbbbbbbb-1-2.md"
    later = dispatches.started(
        held(FIRST, round_number=2), (TIP, BASE, PRIMARY), MOMENT
    )
    assert (later.number, later.round) == (2, 2)


def test_the_reply_of_the_current_dispatch_counts_and_one_it_does_not_name_is_refused() -> (
    None
):
    assert resolved(held(FIRST), 1) == FIRST
    assert code_of(resolved(held(FIRST), 2)) == "brief-seat"
    assert code_of(resolved(held(FIRST), None)) == "brief-seat"
    assert code_of(resolved(held(FIRST), 1, base=OTHER)) == "brief-of"
    assert code_of(resolved(held(), None)) == "brief-of"


def test_a_dispatch_that_a_later_seat_took_the_place_of_is_refused_with_the_one_that_counts() -> (
    None
):
    second = replace(FIRST, number=2, seat=FALLBACK)
    stale = resolved(held(FIRST, second), 1)
    assert isinstance(stale, Refusal)
    assert stale.code == "old-dispatch"
    assert "--dispatch 2" in stale.fix
    assert resolved(held(FIRST, second), 2) == second


def test_a_dispatch_of_an_earlier_round_counts_for_nothing() -> None:
    stale = resolved(held(FIRST, round_number=2), 1)
    assert isinstance(stale, Refusal)
    assert stale.code == "old-dispatch"
    assert "writes the brief of this round" in stale.fix
    later = replace(FIRST, number=2, round=2)
    assert code_of(resolved(held(FIRST, later, round_number=2), 1)) == "old-dispatch"


def test_a_later_base_leaves_the_earlier_bases_dispatch_current() -> None:
    moved = replace(FIRST, number=2, base=OTHER, seat=FALLBACK)
    assert resolved(held(FIRST, moved), 1) == FIRST
    assert resolved(held(FIRST, moved), 2, base=OTHER) == moved


def test_a_dispatch_of_an_earlier_tip_is_left_to_the_steps_old_tip_refusal() -> None:
    earlier = replace(FIRST, tip=OTHER)
    newer = replace(FIRST, number=2, tip=OTHER, seat=FALLBACK)
    record = replace(task("open", **OPENED), landing=held(earlier, newer))
    pinned = dispatches.Pinned(tip=OTHER, base=BASE, dispatch=1)
    assert dispatches.resolved(record, pinned) == earlier
