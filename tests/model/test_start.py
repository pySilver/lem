"""The start of a round and the base under it, over drawn tasks and worlds
(`model/landing/start.py`, `begin.py`, `base.py`, `base_kept.py`, `base_said.py`; `landing.md`
B, E "Recovery", "Relands", "Teammate commit"): an ended task starts no round; an open task's
start is the next round, counted, and any other goes on with the round on record; the mark a
rebase leaves before it is undone whole; and a second rebase is refused only for the tip Lem's
own rebase made that nobody published."""

from typing import TYPE_CHECKING

from hypothesis import given
from hypothesis import strategies as st
from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.landing import base, base_kept, base_said, begin, start
from lem.records.landing.record import Landing
from model.landings import LANDING, any_records, any_worlds, records, worlds
from unit.landing import worlds as plain

if TYPE_CHECKING:
    from lem.model.landing.world import World
    from lem.records.record import Record

WHERE = "/work/fix-the-login"


@LANDING
@given(
    record=records(("landed", "dropped", "answered")),
    world=any_worlds(),
    conflicting=st.booleans(),
)
def test_an_ended_task_starts_no_round(
    record: Record, world: World, *, conflicting: bool
) -> None:
    found = start.decide(record, world, start.Facts(), conflicting=conflicting)
    assert isinstance(found, Refusal)
    assert found.code == "status"


@LANDING
@given(record=any_records(), world=any_worlds(), conflicting=st.booleans())
def test_a_start_begins_the_next_round_of_an_open_task_and_goes_on_with_any_other(
    record: Record, world: World, *, conflicting: bool
) -> None:
    found = start.decide(record, world, start.Facts(), conflicting=conflicting)
    if isinstance(found, Refusal):
        return
    landing = record.landing or Landing()
    opened = landing.phase == "open"
    assert found.round == landing.round + (1 if opened else 0)
    assert (found.branch, found.base_ref) == (world.branch, world.rules.base)
    assert not conflicting or record.task.status == "open"
    begun = begin.begun(record, found)
    after = begun.landing
    assert after is not None
    assert (begun.task.status, begun.task.hold, after.phase) == (
        "landing",
        None,
        "preparing",
    )
    assert after.started == found
    assert after.relands == landing.relands + (1 if opened else 0)
    assert len(begun.journal) == len(record.journal) + (2 if opened else 1)
    if opened:
        assert after.resolution is None


@LANDING
@given(any_records(), worlds())
def test_the_mark_of_a_rebase_is_undone_whole(record: Record, world: World) -> None:
    if record.landing is None:
        return
    marked = base_kept.marked(record, world, world.base)
    mark = (marked.landing or Landing()).based
    assert mark is not None
    assert (mark.tip, mark.before, mark.base) == (
        world.tip or world.base,
        world.tip or world.base,
        world.base,
    )
    assert base_kept.unmarked(marked, record.landing.based) == record


@LANDING
@given(any_records(), any_worlds())
def test_a_second_rebase_is_refused_only_for_the_tip_lem_s_own_unpublished_rebase_made(
    record: Record, world: World
) -> None:
    landing = record.landing or Landing()
    again = base_said.again(record, world, WHERE)
    if again is None:
        return
    based, proposed = landing.based, landing.proposed
    assert based is not None
    assert based.before != based.tip == world.tip
    assert based.tip not in {landing.pushed, proposed.tip if proposed else None}
    assert landing.resolution is None
    assert f"reset --hard {based.before}" in again.fix


@LANDING
@given(
    record=any_records(),
    world=any_worlds(),
    ahead=st.integers(0, 2),
    theirs=st.booleans(),
)
def test_base_refuses_a_teammate_s_commit_and_a_rebase_in_progress(
    record: Record, world: World, ahead: int, *, theirs: bool
) -> None:
    landing = record.landing or Landing()
    commits = ("1234567 a teammate's fix",) if theirs else ()
    found = base.decide(record, world, base.Facts(ahead=ahead, theirs=commits), WHERE)
    if world.rebasing:
        assert isinstance(found, Refusal)
        assert found.code == "rebase-in-progress"
    elif base.foreign(landing, world) and commits:
        assert isinstance(found, Refusal)
        assert found.code == "teammate"
        assert "pull --rebase" in found.fix
    elif found == "onto":
        assert world.base_in_tip
        assert ahead


def test_a_marked_record_with_no_landing_gets_one() -> None:
    record = replace(plain.task(), landing=None)
    marked = base_kept.marked(record, plain.world(), plain.BASE)
    assert marked.landing is not None
    assert base_kept.unmarked(marked, None).landing == Landing()
