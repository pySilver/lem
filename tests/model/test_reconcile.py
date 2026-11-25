"""What a merge call left, over drawn forge answers (`model/landing/reconcile.py`; `landing.md`
C, "In `open`", and E, "Stop or lost reply around the merge call", "Forge took the call",
"Retarget after the locked read", "Closed on GitHub"): an intent on record comes before every
other step, and is replaced only by what the forge shows, the merge into the task's base, the
queue, a definite refusal or a closed request; with only an open request visible it stays, and
the owner is asked."""

from typing import TYPE_CHECKING

from hypothesis import given
from hypothesis import strategies as st
from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.landing import phases, reconcile
from lem.records.landing.merge import MergeAccepted, Merged, Refused
from model.landings import LANDING, any_worlds, opened_landings, pulls
from unit.landing.merges import INTENT, SAME, facing
from unit.landing.worlds import TIP

if TYPE_CHECKING:
    from lem.model.landing.world import PullSeen, World
    from lem.records.landing.merge import MergeIntent
    from lem.records.record import Record

DEQUEUED = st.sampled_from((None, "a required check failed"))
INTENTS = st.sampled_from((INTENT, replace(INTENT, by="owner", via="board")))


@LANDING
@given(opened_landings(), any_worlds(), INTENTS)
def test_an_intent_on_record_is_reconciled_before_any_other_step(
    record: Record, world: World, intent: MergeIntent
) -> None:
    landing = record.landing
    assert landing is not None
    found = phases.due(replace(record, landing=replace(landing, intent=intent)), world)
    assert (found.step, found.by, found.why) == (
        "merge",
        intent.by,
        reconcile.RECONCILED,
    )


@LANDING
@given(opened_landings(), st.none() | pulls(), INTENTS, DEQUEUED)
def test_an_intent_is_replaced_only_by_what_the_forge_shows(
    record: Record, pull: PullSeen | None, intent: MergeIntent, dequeued: str | None
) -> None:
    world = facing(pull=pull)
    found = reconcile.reconciled(record, world, intent, SAME, dequeued=dequeued)
    if pull is None or (pull.state == "open" and not pull.queued and not dequeued):
        assert isinstance(found, Refusal)
        assert found.code == "intent"
        assert "checks" in found.fix
        assert f"--tip {intent.tip}" in found.fix
    elif pull.state == "closed":
        assert found is None
    elif pull.state == "merged":
        reported = pull.merge_commit and pull.merged_head and pull.base_parent
        if pull.base != world.rules.base:
            assert isinstance(found, Refusal)
            assert found.code == "target"
        elif not reported:
            assert isinstance(found, Refusal)
            assert found.code == "unreported"
        else:
            assert isinstance(found, Merged)
            assert (found.by, found.via) == (intent.by, intent.via)
            assert found.merged_head == pull.merged_head
            assert found.destination == world.rules.base
    elif pull.queued:
        assert found == MergeAccepted(tip=intent.tip, at=world.now, queued=pull.queued)
    else:
        assert isinstance(found, Refused)
        assert (found.source, found.line, found.tip) == ("github", dequeued, intent.tip)


@LANDING
@given(opened_landings(), any_worlds())
def test_a_request_the_forge_took_or_ended_is_written_down_before_a_new_call(
    record: Record, world: World
) -> None:
    landing = record.landing
    assert landing is not None
    accepted = MergeAccepted(tip=TIP, at=world.now, queued="in the merge queue")
    for kept in (replace(landing, accepted=accepted), landing):
        pull = world.pull
        if kept.accepted is None and (pull is None or pull.state == "open"):
            continue
        found = phases.due(replace(record, landing=kept), world)
        assert found.step in {"merged", "wait"}
