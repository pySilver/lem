"""A decision about one task among a damaged record of another (decision 30, amended
2026-11-26): it reads the task and the tasks it names, and goes on; a damaged task it names
refuses it with the damaged path."""

from typing import TYPE_CHECKING

import pytest

from fakes.command import lem
from lem.records.work import Plan
from unit.task.spaces import made, read, refusal, workspace

if TYPE_CHECKING:
    from pathlib import Path

    from lem.store.places import Workspace

READ = (
    "--type",
    "feat",
    "--why",
    "a new note",
    "--track",
    "full",
    "--then",
    "interview",
)


def damaged(where: Workspace, slug: str) -> Path:
    """A task `slug` whose record holds no JSON; its path."""
    made(where, slug, status="dropped")
    path = where.state / "tasks" / slug / "task.json"
    path.write_text("{")
    return path


def plan_in(where: Workspace, slug: str) -> None:
    """The plan file of `slug` in its worktree."""
    folder = where.lem / "worktrees" / slug / "docs" / "plans"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"2026-11-25-{slug}.md").write_text("# The plan\n", encoding="utf-8")


def test_a_move_a_build_a_read_a_may_start_and_a_plan_go_on_past_another_task(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    made(where, "good", status="building")
    made(where, "planned-one", status="planned", plan=Plan(path="docs/plans/p.md"))
    made(where, "fresh", status="shaping")
    made(where, "original", status="shaping")
    made(where, "with-plan", status="building")
    plan_in(where, "with-plan")
    damaged(where, "broken")

    ran = (
        lem("task", "move", "good", "ready", cwd=tmp_path),
        lem("task", "build", "planned-one", cwd=tmp_path),
        lem("task", "read", "fresh", *READ, cwd=tmp_path),
        lem("task", "may-start", "original", cwd=tmp_path),
        lem("task", "planned", "with-plan", "--tasks", "2", cwd=tmp_path),
    )

    assert [one.code for one in ran] == [0] * len(ran), ran
    statuses = [read(where, slug).task.status for slug in ("good", "planned-one")]
    assert statuses == ["ready", "building"]


def test_a_damaged_task_that_the_decision_names_refuses_it(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    path = damaged(where, "first")
    made(where, "behind", status="queued", after=("first",))
    made(where, "shaping-one", status="shaping")
    made(where, "resumed", status="building", resumed_from="first")

    ran = {
        "move": lem("task", "move", "behind", "shaping", cwd=tmp_path),
        "may-start": lem("task", "may-start", "behind", cwd=tmp_path),
        "read": lem(
            "task", "read", "shaping-one", *READ, "--after", "first", cwd=tmp_path
        ),
        "planned": lem("task", "planned", "resumed", "--tasks", "2", cwd=tmp_path),
    }

    for name, one in ran.items():
        found = refusal(one)
        assert found["code"] == "unread-task-record", name
        assert str(path) in found["why"], name


def test_a_build_by_plan_file_still_reads_every_task(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    path = damaged(where, "broken")
    made(where, "other", status="planned")
    target = "docs/plans/2026-11-25-other.md"
    found = refusal(lem("task", "build", target, cwd=tmp_path))
    assert found["code"] == "unread-task-record"
    assert str(path) in found["why"]


def test_the_lead_can_read_the_plans_count_and_careful_call(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, "with-plan", status="building")
    plan_in(where, "with-plan")
    recorded = lem(
        "task",
        "planned",
        "with-plan",
        "--tasks",
        "2",
        "--careful",
        "customer data",
        cwd=tmp_path,
    )
    shown = lem("task", "show", "with-plan", cwd=tmp_path)

    assert (recorded.code, shown.code) == (0, 0)
    result = shown.result()
    assert isinstance(result, dict)
    assert result["plan"] == recorded.result()


@pytest.mark.parametrize("name", [".claude", "Bad", "two--parts"])
def test_a_build_by_plan_file_skips_folders_that_cannot_be_tasks(
    tmp_path: Path, name: str
) -> None:
    where = workspace(tmp_path)
    stray = where.state / "tasks" / name / ".cc-writes"
    stray.mkdir(parents=True)
    target = "docs/plans/2026-11-25-other.md"
    made(where, "other", status="planned", plan=Plan(path=target))

    ran = lem("task", "build", target, cwd=tmp_path)

    assert ran.code == 0, ran
    assert read(where, "other").task.status == "building"
    assert stray.is_dir()
