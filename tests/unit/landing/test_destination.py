"""An open pull request keeps the destination recorded when its landing began."""

from typing import TYPE_CHECKING
from unittest.mock import Mock

from msgspec.structs import replace

from lem.app.landing import world as landing_world
from lem.model.landing import merge, reconcile, start
from lem.model.landing.merge_call import Merging
from lem.records.landing.merge import Merged
from unit.landing.merges import BY_MERGER, DONE, SAME, code_of, facing, opened
from unit.landing.worlds import BASE, MOMENT, RULES, SEEN, TREE
from unit.task.spaces import workspace

if TYPE_CHECKING:
    from pathlib import Path


def test_changed_settings_cannot_retarget_the_task_for_a_call_or_an_observed_merge() -> (
    None
):
    record = opened()
    changed = facing(rules=replace(RULES, base="stable"))
    retargeted = replace(changed, pull=replace(SEEN, base="stable"))
    into_stable = replace(DONE, base="stable")
    facts = ("owner", "github", SAME)
    assert code_of(merge.decide(record, retargeted, BY_MERGER, TREE)) == "target"
    assert code_of(reconcile.landed(record, retargeted, into_stable, facts)) == "target"
    assert isinstance(merge.decide(record, changed, BY_MERGER, TREE), Merging)
    adopted = reconcile.landed(record, changed, DONE, facts)
    assert isinstance(adopted, Merged)
    assert adopted.destination == "main"


def test_a_new_round_keeps_the_pull_requests_destination() -> None:
    changed = facing(rules=replace(RULES, base="stable"))
    started = start.decide(opened(), changed, start.Facts(), conflicting=False)
    assert isinstance(started, start.Started)
    assert (started.round, started.base_ref) == (2, "main")


def test_the_world_reads_origin_at_the_tasks_recorded_destination(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path, '[branch]\nbase = "stable"\n')
    ports = Mock()
    ports.git.remote_head.return_value = BASE
    ports.git.tree.return_value = TREE
    found = landing_world.origin(ports, where, opened(), MOMENT)
    ports.git.remote_head.assert_called_once_with(where.checkout, "main")
    assert (found.rules.base, found.base, found.base_tree) == ("main", BASE, TREE)
