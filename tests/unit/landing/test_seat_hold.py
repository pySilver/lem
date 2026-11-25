"""A failed merger seat stops new merge calls and keeps forge bookkeeping available."""

from msgspec.structs import replace

from lem.app.sessions.seats import with_failure
from lem.app.sessions.seats_again import with_again
from lem.model.landing import merge, phases
from lem.model.landing.merge_call import Merging
from lem.records.work import StandIn
from unit.landing.merges import (
    BY_MERGER,
    BY_OWNER,
    DONE,
    INTENT,
    code_of,
    facing,
    opened,
)
from unit.landing.worlds import MOMENT, TREE


def test_a_failed_merger_seat_blocks_dispatch_and_the_locked_call_until_retry() -> None:
    failure = StandIn(seat="merger", failed="claude:opus", error="login", at=MOMENT)
    held = with_failure(opened(), failure=failure)
    world = facing()
    assert phases.due(held, world).step == "wait"
    for asked in (BY_MERGER, BY_OWNER):
        assert code_of(merge.decide(held, world, asked, TREE)) == "seat-blocked"
    retried = with_again(held, seats=frozenset(("merger",)), now=MOMENT)
    assert phases.due(retried, world).step == "merge"
    assert isinstance(merge.decide(retried, world, BY_MERGER, TREE), Merging)


def test_a_failed_merger_seat_keeps_forge_bookkeeping_due() -> None:
    failure = StandIn(seat="merger", failed="claude:opus", error="login", at=MOMENT)
    held = with_failure(opened(intent=INTENT), failure=failure)
    assert phases.due(held, facing(pull=DONE)).step == "merge"
    assert held.landing is not None
    observed = replace(held, landing=replace(held.landing, intent=None))
    assert phases.due(observed, facing(pull=DONE)).step == "merged"
