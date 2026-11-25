"""The task command records and lifts a red-base hold."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from fakes.command import lem
from lem.app.landing.checks_wanted import after_of
from lem.model.landing import phases, start
from lem.records.holds import Blocked
from lem.records.landing.record import Landing
from lem.store import tasks
from unit.landing.worlds import world
from unit.task.spaces import made, read, workspace

if TYPE_CHECKING:
    from pathlib import Path

TASK = "change"
REPAIR = "repair-the-base"
LIFT = ("task", "move", TASK, "ready", "--line", "the base is green again")
LIFT_COMMAND = f'lem task move {TASK} ready --line "the base is green again"'


def test_a_red_base_waits_for_its_repair_then_starts_again(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    original = made(where, TASK, status="landing")
    tasks.update(
        where.state,
        TASK,
        lambda record: replace(record, landing=Landing()),
        original.revision,
    )
    made(where, REPAIR, status="building")

    blocked = lem("task", "red-base", TASK, "--after", REPAIR, cwd=tmp_path)
    assert blocked.envelope()["ok"], blocked
    waiting = read(where, TASK)
    assert waiting.task.status == "ready"
    assert isinstance(waiting.task.hold, Blocked)
    assert after_of(waiting) == (REPAIR,)
    due = phases.due(waiting, world())
    assert due.step == "wait"
    assert LIFT_COMMAND in due.why
    denied = start.entry(waiting, conflicting=False)
    assert denied is not None and denied.code == "held"
    assert LIFT_COMMAND in denied.fix
    without_repair = lem("task", "red-base", TASK, cwd=tmp_path)
    assert without_repair.code == 2
    assert "Missing option '--after'" in without_repair.stderr
    assert read(where, TASK) == waiting

    repair = read(where, REPAIR)
    tasks.update(
        where.state,
        REPAIR,
        lambda record: replace(record, task=replace(record.task, status="landed")),
        repair.revision,
    )
    released = lem(*LIFT, cwd=tmp_path)
    assert released.envelope()["ok"], released
    ready = read(where, TASK)
    assert ready.task.status == "ready"
    assert ready.task.hold is None
    assert phases.due(ready, world()).step == "start"


def test_the_owner_can_clear_a_red_base_after_its_repair_is_dropped(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    made(where, TASK, status="landing")
    made(where, REPAIR, status="building")
    assert lem("task", "red-base", TASK, "--after", REPAIR, cwd=tmp_path).code == 0
    assert lem("task", "move", REPAIR, "dropped", cwd=tmp_path).code == 0
    assert lem("task", "park", TASK, "--why", "wait", cwd=tmp_path).code == 0
    assert lem("task", "resume", TASK, cwd=tmp_path).code == 0
    assert after_of(read(where, TASK)) == (REPAIR,)
    assert phases.due(read(where, TASK), world()).step == "wait"

    moved = lem(*LIFT, cwd=tmp_path)
    assert moved.code == 0, moved
    assert lem("task", "resume", TASK, cwd=tmp_path).code == 1
    ready = read(where, TASK)
    assert ready.task.hold is None
    assert phases.due(ready, world()).step == "start"
