"""The task command records and lifts a red-base hold."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from fakes.command import lem
from lem.app.landing.checks_wanted import after_of
from lem.model.landing import phases
from lem.records.holds import Blocked
from lem.records.landing.record import Landing
from lem.store import tasks
from unit.landing.worlds import world
from unit.task.spaces import made, read, refusal, workspace

if TYPE_CHECKING:
    from pathlib import Path

TASK = "change"
REPAIR = "repair-the-base"


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
    assert after_of(waiting) == REPAIR
    assert phases.due(waiting, world()).step == "wait"

    early = lem("task", "red-base", TASK, cwd=tmp_path)
    assert refusal(early)["code"] == "repair-pending"
    moved = lem("task", "move", TASK, "ready", cwd=tmp_path)
    assert refusal(moved)["code"] == "red-base"
    assert read(where, TASK) == waiting

    repair = read(where, REPAIR)
    tasks.update(
        where.state,
        REPAIR,
        lambda record: replace(record, task=replace(record.task, status="landed")),
        repair.revision,
    )
    released = lem("task", "red-base", TASK, cwd=tmp_path)
    assert released.envelope()["ok"], released
    ready = read(where, TASK)
    assert ready.task.status == "ready"
    assert ready.task.hold is None
    assert phases.due(ready, world()).step == "start"
