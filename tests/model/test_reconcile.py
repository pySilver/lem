"""What a merge call left, over drawn forge answers (`model/landing/reconcile.py`; `landing.md`
C, "In `open`", and E, "Stop or lost reply around the merge call", "Forge took the call",
"Retarget after the locked read", "Closed on GitHub"): an intent on record comes before every
other step, and is replaced only by what the forge shows, the merge into the task's base, the
queue, a definite refusal or a closed request; with only an open request visible it stays, and
the owner is asked."""

from datetime import timedelta
from typing import TYPE_CHECKING

from hypothesis import given
from hypothesis import strategies as st
from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.landing import phases, reconcile
from lem.model.landing.queue_evidence import Event
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
    if world.pull and world.pull.state != "open":
        assert found.step == "merged"
        return
    assert (found.step, found.by, found.why) == (
        "merge",
        intent.by,
        "a merge call is on record: it is reconciled first",
    )


@LANDING
@given(opened_landings(), st.none() | pulls(), INTENTS, DEQUEUED)
def test_an_intent_is_replaced_only_by_what_the_forge_shows(
    record: Record, pull: PullSeen | None, intent: MergeIntent, dequeued: str | None
) -> None:
    if pull is not None:
        entered = Event(id="added", at=intent.at + timedelta(seconds=1), head=pull.head)
        reported_event = (
            replace(entered, id="removed") if dequeued and not pull.queued else entered
        )
        pull = replace(
            pull, dequeued=dequeued, queue_entered=entered, queue_event=reported_event
        )
    assert record.landing is not None
    record = replace(record, landing=replace(record.landing, intent=intent))
    world = facing(pull=pull)
    found = reconcile.reconciled(record, world, intent, SAME)
    if pull is None or (
        pull.state == "open"
        and (pull.head != intent.tip or (not pull.queued and not dequeued))
    ):
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
            expected = (
                (intent.by, intent.via)
                if intent.tip == pull.merged_head
                else ("owner", "github")
            )
            assert (found.by, found.via) == expected
            assert found.merged_head == pull.merged_head
            assert found.destination == world.rules.base
    elif pull.queued:
        assert found == MergeAccepted(
            tip=intent.tip,
            at=intent.at,
            queued=pull.queued,
            by=intent.by,
            via=intent.via,
            queue_before=intent.queue_before,
        )
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
