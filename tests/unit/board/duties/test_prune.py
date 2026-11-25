"""`lem prune` and the server's hourly run of it: the days of `state.keep_days`, the developer's
own over the team's in both orders and from a task's worktree, `--days` with a dry run only, the
log line of a run that did something and none for a quiet one, and the run at the first tick,
then each hour."""

import json
from datetime import timedelta
from typing import TYPE_CHECKING

import pytest

from fakes.records import MOMENT, record
from lem.board.duties import prune
from lem.board.duties.memory import Kept
from lem.cli import lazy
from lem.cli.prune import days
from lem.kernel import clock
from lem.kernel.errors import Refusal
from lem.store import tasks
from lem.store.retention import run
from unit.board.duties.world import duty_of
from unit.sessions.world import here_of

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path

    from lem.app.sessions.here import Here
    from lem.store.retention.answer import Pruned

HOUR = timedelta(seconds=3600)
NOW = MOMENT + timedelta(days=100)


def settings(here: Here, team: int | None, local: int | None) -> None:
    """The team's and the developer's `state.keep_days`, when each is named."""
    lem = here.where.checkout / ".lem"
    for name, kept in (("settings.toml", team), ("settings.local.toml", local)):
        if kept is not None:
            (lem / name).write_text(f"[state]\nkeep_days = {kept}\n")


def old_task(here: Here, slug: str = "old-task") -> None:
    """A task that landed long ago, with a file beside its small record."""
    tasks.create(here.where.state, record(slug, status="landed", since=MOMENT))
    (here.folder(slug) / "handoff.md").write_text("handoff\n")


def lem(
    capsys: pytest.CaptureFixture[str], where: Path, *argv: str
) -> dict[str, object]:
    """`lem --repo WHERE ARGV` in this process: its envelope, with its exit code."""
    code = lazy.main(["--repo", str(where), *argv])
    return {**json.loads(capsys.readouterr().out), "code": code}


@pytest.mark.parametrize(
    ("team", "local", "kept", "source"),
    [
        (10, 3, 3, ".lem/settings.local.toml"),
        (3, 10, 10, ".lem/settings.local.toml"),
        (10, None, 10, ".lem/settings.toml"),
        (None, None, 30, "Lem's default"),
    ],
)
def test_the_days_are_the_developers_own_over_the_teams_and_say_where_they_come_from(
    tmp_path: Path, team: int | None, local: int | None, kept: int, source: str
) -> None:
    here = here_of(tmp_path)
    settings(here, team, local)
    assert days.kept(here.where.checkout, None, dry=False) == (kept, source)
    assert days.kept(here.where.checkout, 2, dry=True) == (2, "--days 2")


def test_days_go_with_a_dry_run_only_and_are_never_below_none(tmp_path: Path) -> None:
    with pytest.raises(Refusal) as wet:
        days.kept(tmp_path, 5, dry=False)
    assert wet.value.code == "days"
    with pytest.raises(Refusal) as below:
        days.kept(tmp_path, -1, dry=True)
    assert below.value.why == "--days -1 is no number of days"


def test_lem_prune_removes_by_the_settings_and_its_dry_run_by_days(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    here = here_of(tmp_path)
    settings(here, 7, None)
    tasks.create(
        here.where.state,
        record("old-task", status="landed", since=clock.now() - timedelta(days=8)),
    )
    (here.folder("old-task") / "handoff.md").write_text("handoff\n")
    dry = lem(capsys, here.where.checkout, "prune", "--dry-run", "--days", "10")
    assert dry["code"] == 0
    assert dry["result"]["from"] == "--days 10"
    assert dry["result"]["files"] == 0
    wet = lem(capsys, here.where.checkout, "prune")
    assert (wet["code"], wet["result"]["from"], wet["result"]["files"]) == (
        0,
        ".lem/settings.toml",
        1,
    )
    assert str(wet["say"]).startswith("removed 1 files of 1 ended tasks")
    refused = lem(capsys, here.where.checkout, "prune", "--days", "3")
    assert (refused["code"], refused["refusal"]["code"]) == (1, "days")


def test_lem_prune_from_a_tasks_worktree_keeps_the_main_checkouts_state(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    here = here_of(tmp_path / "shop")
    settings(here, 7, 3)
    linked = here.where.checkout / ".git" / "worktrees" / "gift-note"
    linked.mkdir(parents=True)
    (linked / "commondir").write_text("../..\n")
    worktree = here.where.checkout / ".lem" / "worktrees" / "gift-note"
    worktree.mkdir(parents=True)
    (worktree / ".git").write_text(f"gitdir: {linked}\n")
    said = lem(capsys, worktree, "prune", "--dry-run")
    assert said["result"]["state"] == str(here.where.state)
    assert (said["result"]["keep_days"], said["result"]["from"]) == (
        3,
        ".lem/settings.local.toml",
    )


def test_a_failed_removal_is_a_refusal_that_names_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    here = here_of(tmp_path)
    tasks.create(
        here.where.state,
        record("old-task", status="landed", since=clock.now() - timedelta(days=40)),
    )
    checks = here.folder("old-task") / "checks"
    checks.mkdir()
    (checks / "1-make.txt").write_text("output\n")
    checks.chmod(0o500)
    try:
        said = lem(capsys, here.where.checkout, "prune")
    finally:
        checks.chmod(0o700)
    assert (said["code"], said["refusal"]["code"]) == (1, "prune-failed")
    assert "tasks/old-task/checks/1-make.txt: " in said["refusal"]["why"]
    again = lem(capsys, here.where.checkout, "prune")
    assert (again["code"], again["result"]["files"]) == (0, 1)


def test_it_runs_at_the_first_tick_then_each_hour(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    here = here_of(tmp_path)
    runs: list[object] = []
    pruned = run.pruned

    def counted(
        state: Path, keep: int, source: str, now: datetime, *, dry: bool
    ) -> Pruned:
        runs.append(now)
        return pruned(state, keep, source, now, dry=dry)

    monkeypatch.setattr(run, "pruned", counted)
    kept = Kept()
    for moment in (NOW, NOW + HOUR - timedelta(seconds=1), NOW + HOUR):
        prune.tick(duty_of(here, moment, kept))
    assert len(runs) == 2


def test_the_log_says_what_a_run_removed_skipped_and_failed_and_nothing_for_a_quiet_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    here = here_of(tmp_path)
    prune.tick(duty_of(here, NOW))
    assert capsys.readouterr().err == ""
    old_task(here)
    (here.where.state / "tasks" / "a-link").symlink_to(tmp_path)
    prune.tick(duty_of(here, NOW))
    said = capsys.readouterr().err
    assert said.startswith(
        "lem serve: shop: lem prune: removed 1 files of 1 ended tasks"
    )
    assert (
        "; skipped tasks/a-link: a link, which prune never follows and never removes"
        in said
    )


def test_a_run_that_removed_only_an_empty_file_has_its_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    here = here_of(tmp_path)
    old_task(here)
    (here.folder("old-task") / "handoff.md").write_text("")
    prune.tick(duty_of(here, NOW))
    assert "removed 1 files" in capsys.readouterr().err
