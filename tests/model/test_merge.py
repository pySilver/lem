"""The invariants before an effect, over drawn open landings, worlds and asks
(`model/landing/merge.py`, `merge_evidence.py`, `merge_asked.py`, `invariants.py`; `landing.md`
H 1, 2 and 4): a merge the model lets go names the open pull request into the task's base at the
proposed tip Lem pushed, a tip a passed run of the checks covers with the definitions as now, a
base the checks or a safe read covered, and an authority; a push is due only for a tip the checks
cover."""

from datetime import timedelta
from typing import TYPE_CHECKING

from hypothesis import given
from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.landing import (
    checks,
    merge,
    merge_standing,
    mergeread,
    phases,
)
from lem.model.landing.world import Held
from lem.records.landing.record import Landing
from model.landings import (
    LANDING,
    any_records,
    any_worlds,
    asks,
    checks_trees,
    facing_worlds,
    opened_landings,
)
from unit.landing.merges import BY_MERGER, facing, opened
from unit.landing.worlds import APPROVED, CRITERION, TREE

if TYPE_CHECKING:
    from lem.model.landing.merge_asked import Asked
    from lem.model.landing.world import World
    from lem.records.record import Record


def merges(
    record: Record, world: World, asked: Asked, checks_tree: str
) -> merge.merge_call.Merging | None:
    """The merge the model lets go, or None when it refuses."""
    found = merge.decide(record, world, asked, checks_tree)
    return None if isinstance(found, Refusal) else found


@LANDING
@given(opened_landings(), facing_worlds(), asks(), checks_trees())
def test_a_merge_goes_only_through_the_open_request_at_the_proposed_tip_lem_pushed(
    record: Record, world: World, asked: Asked, checks_tree: str
) -> None:
    going = merges(record, world, asked, checks_tree)
    if going is None:
        return
    landing = record.landing or Landing()
    proposed, pull, kept = landing.proposed, world.pull, landing.pull
    assert record.task.status == "open"
    assert proposed is not None
    assert pull is not None
    assert kept is not None
    assert (pull.state, pull.base, pull.url) == ("open", world.rules.base, kept.url)
    assert pull.head == proposed.tip == world.tip == landing.pushed == going.intent.tip
    assert world.rules.base not in world.rules.protected
    assert isinstance(checks.holds(record, world), Held)


@LANDING
@given(opened_landings(), facing_worlds(), asks(), checks_trees())
def test_a_merge_goes_only_onto_a_base_the_checks_or_a_safe_read_covered(
    record: Record, world: World, asked: Asked, checks_tree: str
) -> None:
    if merges(record, world, asked, checks_tree) is None:
        return
    landing = record.landing or Landing()
    if asked.by == "owner" or landing.standing is not None:
        assert landing.checked is not None
        assert landing.checked.base == world.base
        return
    if world.base_tree == checks_tree:
        return
    read = mergeread.latest(landing, world.base_tree)
    assert read is not None
    assert (read.base_call, read.base_tree) == ("safe", world.base_tree)


@LANDING
@given(opened_landings(), facing_worlds(), asks(), checks_trees())
def test_a_merge_goes_only_with_the_merger_s_authority_or_the_owner_s_word(
    record: Record, world: World, asked: Asked, checks_tree: str
) -> None:
    if merges(record, world, asked, checks_tree) is None:
        return
    landing = record.landing or Landing()
    proposed = landing.proposed
    assert proposed is not None
    if asked.by == "merger":
        assert merge.authority(record, world) is None
        assert not merge_standing.reasons_now(record)
        assert not merge.careful(record)
        assert world.rules.land == "agent"
        read = mergeread.latest(landing, world.base_tree)
        assert read is not None
        assert read.verdict == "merge"
    elif asked.standing:
        assert merge_standing.standing_of(record) is not None
    else:
        assert asked.tip == proposed.tip
    refused = landing.refused
    if refused is not None and refused.source == "github":
        assert refused.tip != proposed.tip or (asked.by, asked.standing) == (
            "owner",
            False,
        )


def test_approval_of_changed_criteria_refuses_an_otherwise_valid_agent_merge() -> None:
    record = opened()
    world = facing()
    assert isinstance(
        merge.decide(record, world, BY_MERGER, TREE), merge.merge_call.Merging
    )

    later = replace(
        APPROVED,
        number=2,
        by="owner",
        replaces=APPROVED.number,
        at=APPROVED.at + timedelta(seconds=1),
        criteria=(replace(CRITERION, text="The login takes a code."),),
    )
    criteria = replace(
        record.task.criteria, approvals=(APPROVED, later), criteria=later.criteria
    )
    changed = replace(record, task=replace(record.task, criteria=criteria))
    found = merge.decide(changed, world, BY_MERGER, TREE)
    assert isinstance(found, Refusal)
    assert found.code == "merger-rule"


@LANDING
@given(opened_landings(), facing_worlds())
def test_the_merge_agent_is_due_to_merge_only_with_its_own_authority(
    record: Record, world: World
) -> None:
    found = phases.due(record, world)
    if found.step == "merge" and found.by == "merger":
        landing = record.landing or Landing()
        assert landing.intent is not None or merge.authority(record, world) is None


@LANDING
@given(any_records(), any_worlds())
def test_a_push_is_due_only_for_a_tip_a_passed_run_of_the_checks_covers(
    record: Record, world: World
) -> None:
    if phases.due(record, world).step == "propose":
        assert isinstance(checks.holds(record, world), Held)
