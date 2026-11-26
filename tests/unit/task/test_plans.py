"""A task's plan: the name of its file from `[paths]`, the plan it has (a resumed task's is the
old task's until it writes one), `lem task planned` from `building` to `planned`, and
`lem task build` by a slug, by a plan file, or with no name the plans that wait
(`project.cmd_plan_file`, `plans.py` and `stages/start.md`, "`/lem build`", on `main`)."""

from datetime import date
from typing import TYPE_CHECKING

import pytest

from fakes.command import lem
from fakes.records import MOMENT
from lem.app.tasks import building, lineage, planned, plans
from lem.kernel.errors import Refusal
from lem.model.task import plans as names
from lem.records.holds import Parked
from lem.records.journal.task import StateNoted
from lem.records.task import Shape
from lem.records.work import Plan
from lem.settings.load import settings_of
from lem.store import places
from unit.task import spaces

if TYPE_CHECKING:
    from pathlib import Path

    from lem.store.places import Workspace

SLUG = "gift-note"
DAY = date(2026, 11, 25)
WORDS = Plan(path="", tasks=3)


def plan_in(where: Workspace, slug: str, name: str) -> None:
    """A plan file `name` in the plans folder of the worktree of `slug`."""
    folder = where.lem / "worktrees" / slug / "docs" / "plans"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text("# The plan\n", encoding="utf-8")


def test_the_name_from_the_pattern_and_the_day() -> None:
    assert names.name(names.PLAN_FILE, SLUG, DAY) == "2026-11-25-gift-note.md"
    assert names.name("<slug>-DD.MM.YYYY.md", SLUG, DAY) == "gift-note-25.11.2026.md"
    form = names.regex(names.PLAN_FILE, None)
    found = form.fullmatch("2026-11-25-gift-note-in-export.md")
    assert found is not None
    assert found["slug"] == "gift-note-in-export"


def test_the_newest_plan_of_the_task_or_of_the_one_it_came_from() -> None:
    files = (
        "2026-11-20-gift-note.md",
        "2026-11-24-gift-note.md",
        "2026-11-24-gift-note-in-export.md",
        "notes.md",
    )
    newest = names.newest(files, names.PLAN_FILE, (SLUG,))
    assert newest == "2026-11-24-gift-note.md"
    assert names.newest(files, names.PLAN_FILE, ("gift-note-2", SLUG)) == newest
    assert names.newest(files, names.PLAN_FILE, ("other",)) is None


def test_a_day_that_is_no_day_is_refused() -> None:
    assert names.day_of(None, DAY) == DAY
    assert names.day_of("2026-01-05", DAY) == date(2026, 1, 5)
    for given in ("2026-13-01", "25.11.2026", "20261125", "2026-1-5"):
        with pytest.raises(Refusal) as caught:
            names.day_of(given, DAY)
        assert caught.value.why == f"--date {given!r} is not a day as YYYY-MM-DD"


def test_the_command_names_the_plan_and_finds_the_one_written(tmp_path: Path) -> None:
    where = spaces.workspace(tmp_path / "repo")
    spaces.made(where, SLUG, status="building")
    ran = lem("task", "plan-file", SLUG, "--date", "2026-11-25", cwd=where.checkout)
    assert ran.code == 0, ran.stderr
    assert ran.result() == {
        "slug": SLUG,
        "pattern": "YYYY-MM-DD-<slug>.md",
        "name": "2026-11-25-gift-note.md",
        "path": "docs/plans/2026-11-25-gift-note.md",
    }
    plan_in(where, SLUG, "2026-11-24-gift-note.md")
    named = plans.plan_file(where, SLUG, "2026-11-25")
    assert named.found == "docs/plans/2026-11-24-gift-note.md"


def test_the_pattern_and_the_folder_come_from_the_settings(tmp_path: Path) -> None:
    settings = spaces.SETTINGS + '\n[paths]\nplans = "plans"\nplan_file = "<slug>.md"\n'
    where = spaces.workspace(tmp_path / "repo", settings)
    spaces.made(where, SLUG, status="building")
    named = plans.plan_file(where, SLUG, None)
    assert (named.name, named.path) == ("gift-note.md", "plans/gift-note.md")
    wrong = spaces.workspace(tmp_path / "wrong", '[paths]\nplan_files = "x"\n')
    with pytest.raises(Refusal) as caught:
        settings_of(wrong.checkout)
    assert caught.value.code == "settings-key"
    assert "did you mean plan_file?" in caught.value.fix


def test_a_resumed_task_finds_the_plan_of_the_task_it_came_from(tmp_path: Path) -> None:
    where = spaces.workspace(tmp_path / "repo")
    spaces.made(where, SLUG, status="dropped")
    resumed = spaces.made(where, "gift-note-2", status="building", resumed_from=SLUG)
    plan_in(where, "gift-note-2", "2026-11-20-gift-note.md")
    every = (spaces.read(where, SLUG), resumed)
    assert names.chain("gift-note-2", every) == ("gift-note-2", SLUG)
    older = lineage.lineage(where.state, resumed)
    assert plans.found(where, resumed, older) == "docs/plans/2026-11-20-gift-note.md"
    plan_in(where, "gift-note-2", "2026-11-21-gift-note-2.md")
    chained = names.chain("gift-note-2", every)
    assert (
        plans.found(where, resumed, chained) == "docs/plans/2026-11-21-gift-note-2.md"
    )


def test_planned_records_the_plan_and_moves_the_task(tmp_path: Path) -> None:
    where = spaces.workspace(tmp_path / "repo")
    spaces.made(where, SLUG, status="building")
    plan_in(where, SLUG, "2026-11-25-gift-note.md")
    words = Plan(path="", tasks=4, careful="the export a shop reads", large=True)
    plan = planned.planned(where, SLUG, words)
    assert plan == Plan(
        path="docs/plans/2026-11-25-gift-note.md",
        tasks=4,
        careful="the export a shop reads",
        large=True,
    )
    after = spaces.read(where, SLUG)
    assert (after.task.status, after.task.plan) == ("planned", plan)
    entry = after.journal[-1]
    assert isinstance(entry, StateNoted)
    assert entry.line == "plan committed: 4 tasks"


def test_planned_is_refused_with_no_plan_no_task_or_another_status(
    tmp_path: Path,
) -> None:
    where = spaces.workspace(tmp_path / "repo")
    spaces.made(where, SLUG, status="building")
    with pytest.raises(Refusal) as none:
        planned.planned(where, SLUG, WORDS)
    assert none.value.code == "no-plan"
    assert f"lem task plan-file {SLUG}" in none.value.fix
    plan_in(where, SLUG, "2026-11-25-gift-note.md")
    with pytest.raises(Refusal) as empty:
        planned.planned(where, SLUG, Plan(path="", tasks=0))
    assert empty.value.code == "plan-tasks"
    spaces.made(where, "shaped", status="shaping")
    with pytest.raises(Refusal) as shaping:
        planned.planned(where, "shaped", WORDS)
    assert shaping.value.code == "move"


def test_a_standard_track_task_needs_a_plan_even_with_criteria_in_its_folder(
    tmp_path: Path,
) -> None:
    where = spaces.workspace(tmp_path / "repo")
    shape = Shape(type="feat", why="the export has a new field", track="full")
    spaces.made(where, SLUG, status="building", shape=shape)
    worktree = where.lem / "worktrees" / SLUG
    (worktree / ".git").mkdir(parents=True)
    sheet = places.task_folder(where.state, SLUG) / "criteria.md"
    sheet.write_text(
        "## Acceptance criteria\n\nSize: full, because the export changes.\n\n"
        "1. Order 1042 has its gift note in the CSV row.\n"
        "   - no test: the owner checks the CSV file.\n"
    )
    shown = lem("criteria", "show", SLUG, cwd=where.checkout)
    assert spaces.refusal(shown)["code"] == "not-small"
    with pytest.raises(Refusal) as caught:
        planned.planned(where, SLUG, WORDS)
    assert caught.value.code == "no-plan"
    assert spaces.read(where, SLUG).task.plan is None


def test_build_takes_a_slug_or_a_plan_file(tmp_path: Path) -> None:
    where = spaces.workspace(tmp_path / "repo")
    path = "docs/plans/2026-11-25-gift-note.md"
    spaces.made(where, SLUG, status="planned", plan=Plan(path=path, tasks=2))
    spaces.made(where, "label", status="planned", plan=Plan(path="docs/plans/x.md"))
    started = building.built(where, f"/somewhere/{path}")
    assert (started.slug, started.plan, started.status) == (SLUG, path, "building")
    assert spaces.read(where, SLUG).task.status == "building"
    by_slug = building.built(where, "label")
    assert (by_slug.slug, by_slug.status) == ("label", "building")
    spaces.made(where, "by-name", status="planned")
    assert building.built(where, "2026-11-20-by-name.md").slug == "by-name"


def test_build_with_no_name_lists_the_plans_that_wait(tmp_path: Path) -> None:
    where = spaces.workspace(tmp_path / "repo")
    path = "docs/plans/2026-11-25-gift-note.md"
    spaces.made(
        where, SLUG, ask="the gift note", status="planned", plan=Plan(path=path)
    )
    spaces.made(where, "running", status="building")
    listed = building.built(where, None)
    assert listed.waiting == (
        building.Waiting(slug=SLUG, ask="the gift note", plan=path),
    )
    ran = lem("task", "build", cwd=where.checkout)
    assert ran.code == 0, ran.stderr
    assert ran.result() == {
        "waiting": [{"slug": SLUG, "ask": "the gift note", "plan": path}]
    }


def test_build_refuses_a_task_that_is_not_planned(tmp_path: Path) -> None:
    where = spaces.workspace(tmp_path / "repo")
    spaces.made(where, SLUG, status="planned", plan=Plan(path="docs/plans/a.md"))
    spaces.made(where, "running", status="building")
    spaces.made(where, "behind", status="queued", after=("running",))
    spaces.made(where, "aside", status="planned", hold=Parked(since=MOMENT))
    with pytest.raises(Refusal) as running:
        building.built(where, "running")
    assert running.value.code == "not-planned"
    assert running.value.fix.endswith(f"(lem task build SLUG): aside, {SLUG}")
    with pytest.raises(Refusal) as queued:
        building.built(where, "behind")
    assert 'lem task start behind --words "HIS WORDS"' in queued.value.fix
    with pytest.raises(Refusal) as parked:
        building.built(where, "aside")
    assert parked.value.code == "parked"
    with pytest.raises(Refusal) as unknown:
        building.built(where, "docs/plans/notes.md")
    assert unknown.value.code == "no-plan"
