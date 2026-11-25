"""`lem settings show` beyond the values: each seat's parts, the experts and whether each can
answer on this machine, the load gate, the places from any folder, and the main checkout's
settings in a task's worktree."""

from typing import TYPE_CHECKING

import pytest
import tomlkit

from fakes.command import lem
from fakes.repo import RealRepo, run_git
from lem.settings import edit
from lem.settings.machine import Load
from lem.settings.show import load_now, shown
from unit.settings.given import given

if TYPE_CHECKING:
    from pathlib import Path


def test_each_seat_is_read_into_its_parts_and_an_off_fallback_is_none(
    tmp_path: Path,
) -> None:
    team = "[seats]\nmerger = 'codex'\nsession = 'claude:high'\nfallback = false\n"
    setup = given(tmp_path, team=team)
    found = shown(setup.checkout, setup.environ)
    assert found.seats["merger"] is not None
    assert (found.seats["merger"].agent, found.seats["merger"].model) == ("codex", None)
    assert found.seats["session"] is not None
    assert found.seats["session"].effort == "high"
    assert found.seats["fallback"] is None
    assert found.seats["reviewer"] is not None
    assert found.seats["reviewer"].model == "opus"


def test_an_expert_answers_only_where_its_agent_is_on_the_machine(
    tmp_path: Path,
) -> None:
    setup = given(tmp_path)
    without = shown(setup.checkout, setup.environ)
    assert [(one.place, one.here) for one in without.experts] == [
        ("fable", True),
        ("astra", False),
    ]
    codex = tmp_path / "bin" / "codex"
    codex.parent.mkdir(parents=True, exist_ok=True)
    codex.write_text("#!/bin/sh\nexit 0\n")
    codex.chmod(0o755)
    with_codex = shown(setup.checkout, setup.environ)
    assert [one.here for one in with_codex.experts] == [True, True]


def test_one_expert_answers_in_the_first_place(tmp_path: Path) -> None:
    setup = given(tmp_path, local="[seats]\nexperts = ['codex/gpt-6.2-astra:high']\n")
    found = shown(setup.checkout, setup.environ)
    assert [(one.place, one.agent) for one in found.experts] == [("fable", "codex")]
    assert found.sources["seats.experts"] == ".lem/settings.local.toml"


@pytest.mark.parametrize(
    ("start", "gate"),
    [
        (0.0, None),
        (10_000.0, "open"),
        (0.001, "closed: the checks wait for a load below 0.001"),
    ],
    ids=("away", "open", "closed"),
)
def test_the_load_gate_is_open_closed_or_away(start: float, gate: str | None) -> None:
    found = load_now(Load(start=start))
    assert found.gate == gate
    assert found.now >= 0


def test_in_a_tasks_worktree_every_table_is_the_main_checkouts(tmp_path: Path) -> None:
    team = b"[branch]\nbase = 'main'\n[flow]\ntopics = ['money is lost']\n"
    repo = RealRepo.init(tmp_path / "repo", {".lem/settings.toml": team})
    worktree = repo.checkout / ".lem" / "worktrees" / "lift-it"
    run_git(repo.checkout, "worktree", "add", "--quiet", "-b", "lift-it", str(worktree))
    (worktree / ".lem" / "settings.toml").write_text(
        "[flow]\ntopics = []\n[naps]\non = true\n"
    )
    found = lem("settings", "show", cwd=worktree).result()
    assert isinstance(found, dict)
    assert found["settings"]["flow"]["topics"] == ["money is lost"]
    assert found["settings"]["naps"]["on"] is False
    assert found["checkout"] == str(repo.checkout.resolve())


def test_the_main_checkout_is_found_whole_when_its_path_holds_a_line_break(
    tmp_path: Path,
) -> None:
    repo = RealRepo.init(tmp_path / "two\nlines", {".lem/settings.toml": b""})
    worktree = repo.checkout / ".lem" / "worktrees" / "x"
    run_git(repo.checkout, "worktree", "add", "--quiet", "-b", "x", str(worktree))
    ran = lem("settings", "set", "naps.on", "false", "--local", cwd=worktree)
    assert ran.code == 0, ran.stdout
    assert (repo.checkout / ".lem" / "settings.local.toml").is_file()


def test_a_path_outside_any_checkout_is_refused(tmp_path: Path) -> None:
    ran = lem("path", "profile", cwd=tmp_path)
    assert ran.code == 1
    assert ran.envelope()["refusal"]["code"] == "no-repository"


def test_reviewer_is_no_command_and_writes_nothing(tmp_path: Path) -> None:
    repo = RealRepo.init(tmp_path / "repo", {".lem/settings.toml": b""})
    ran = lem("settings", "reviewer", "codex/a:high", cwd=repo.checkout)
    assert ran.code == 2
    assert not (repo.checkout / ".lem" / "settings.local.toml").exists()


def test_the_edit_of_a_file_is_tomlkits_the_well_known_library() -> None:
    assert edit.tomlkit is tomlkit
