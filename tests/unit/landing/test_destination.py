"""An open pull request keeps the destination recorded when its landing began."""

from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest
from msgspec.structs import replace

from lem.app.landing import world as landing_world
from lem.kernel.errors import Refusal
from lem.model.landing import destination, merge, reconcile, start
from lem.model.landing.merge_call import Merging
from lem.records.landing.merge import Merged
from unit.landing.merges import BY_MERGER, DONE, SAME, code_of, facing, opened
from unit.landing.worlds import BASE, MOMENT, RULES, SEEN, TREE, task
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


def test_origin_without_the_recorded_base_refuses_the_landing(tmp_path: Path) -> None:
    where = workspace(tmp_path, '[branch]\nbase = "stable"\n')
    ports = Mock()
    ports.git.remote_head.return_value = None
    with pytest.raises(Refusal) as error:
        landing_world.origin(ports, where, opened(), MOMENT)
    refused = error.value
    assert (refused.code, refused.why, refused.fix) == (
        "no-base",
        "origin has no branch main, the base of the task",
        "push main to origin, then run the step again",
    )


def test_origin_uses_the_settings_until_a_task_starts_its_landing(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path, '[branch]\nbase = "stable"\n')
    ports = Mock()
    ports.git.remote_head.return_value = BASE
    ports.git.tree.return_value = TREE
    found = landing_world.origin(ports, where, task("ready"), MOMENT)
    ports.git.remote_head.assert_called_once_with(where.checkout, "stable")
    assert found.rules.base == "stable"


def test_a_forge_pull_cannot_stand_in_for_a_pull_the_task_did_not_record() -> None:
    record = task("ready")
    found = destination.same_pull(record, (SEEN.number, SEEN.url))
    assert found is not None and found.code == "no-pull"
    assert found.why == f"the forge shows {SEEN.url}, not the pull request on record"
