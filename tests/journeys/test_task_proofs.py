"""A task's worktree and claims on a throwaway repository."""

import io
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from fakes.command import lem
from fakes.repo import git_env, run_git
from journeys.agent import BUILDING, ok, refused, through
from journeys.test_park_drop import drop, tripped
from journeys.test_skeleton import BRANCH, SLUG, made
from lem.adapters.git_cli import GitCli
from lem.board.views.branch import head_of
from lem.board.views.world import Place
from lem.kernel import clock, paths
from lem.model.task import tickets
from lem.records.tickets import Ticket, TicketStep
from lem.store import places, tasks

if TYPE_CHECKING:
    from lem.records.record import Record

type Capsys = pytest.CaptureFixture[str]


def test_lems_own_setup_installs_the_suite_in_its_new_worktree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if not os.environ.get("UV_CACHE_DIR"):
        pytest.skip(
            "give UV_CACHE_DIR with the locked packages for a fresh offline install"
        )
    monkeypatch.setenv("UV_OFFLINE", "1")
    monkeypatch.setenv("UV_PYTHON", sys.executable)
    checkout = (tmp_path / "lem").resolve()
    checkout.mkdir()
    archived = subprocess.check_output(
        ["git", "archive", "HEAD"], cwd=paths.root(), env=git_env()
    )
    with tarfile.open(fileobj=io.BytesIO(archived)) as tree:
        tree.extractall(checkout, filter="data")
    run_git(checkout, "init", "--quiet", "-b", "main")
    run_git(checkout, "add", "--all")
    run_git(checkout, "commit", "--quiet", "-m", "chore: copy Lem for the proof")
    assert lem("task", "open", SLUG, "--ask", "a word", cwd=checkout).code == 0
    worktree = lem("task", "worktree", SLUG, "--branch", BRANCH, cwd=checkout)
    log = places.task_folder(checkout / places.STATE, SLUG) / "setup.log"
    assert worktree.code == 0, worktree.stdout + (
        log.read_text() if log.exists() else ""
    )
    made = worktree.envelope()["result"]
    assert isinstance(made, dict)
    assert made["setup"] == [{"command": "uv sync --locked", "exit": 0}]
    local = Path(made["worktree"])
    version = subprocess.check_output([local / ".venv/bin/lem", "version"], cwd=local)
    assert json.loads(version)["root"] == str(local)
    checks = subprocess.check_output(
        [
            local / ".venv/bin/python",
            "-I",
            "-B",
            "tests",
            "--level",
            "unit",
            "tests/unit/core/test_repository.py",
        ],
        cwd=local,
    )
    assert b"skipped 0, failed 0" in checks


def test_a_move_from_a_worktree_keeps_its_branch_and_the_board_reads_its_tip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    through(capsys, world, BUILDING)
    subject = "fix: 0123 is a string"
    run_git(world.worktree, "commit", "--allow-empty", "-m", subject)
    tip = run_git(world.worktree, "rev-parse", "HEAD")
    ok(
        capsys,
        world,
        "task",
        "move",
        SLUG,
        "ready",
        "--line",
        "the report is written",
        inside=True,
    )
    record = tasks.read(world.checkout / places.STATE, SLUG)
    assert record.task.status == "ready"
    assert record.task.branch == run_git(world.worktree, "branch", "--show-current")
    place = Place(repo="lines", base="main", path=str(world.checkout))
    found = head_of(GitCli(environ=git_env()), world.checkout, record.task, place)
    assert found is not None and (found.sha, found.subject) == (tip, subject)


def test_a_refused_open_or_resume_leaves_the_ticket_where_it_was(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    through(capsys, world, BUILDING)
    team = world.checkout / ".lem" / "settings.toml"
    with team.open("a") as written:
        written.write('\n[tracker]\nkind = "github"\n')
    repo = ("--ticket-repo", "acme/shop")
    issue = ("--ticket", "12", *repo)
    opening = ("task", "open")
    collision = refused(
        capsys, world, *opening, SLUG, "--ask", "an export issue", *issue
    )
    assert collision["code"] == "task-exists"
    claimed = ok(
        capsys, world, *opening, "export-issue", "--ask", "an export issue", *issue
    )
    assert claimed["result"]["slug"] == "export-issue"
    state = world.checkout / places.STATE
    assert tasks.read(state, SLUG).task.ticket is None
    issued = tasks.read(state, "export-issue").task.ticket
    assert issued is not None and issued.id == "#12"

    ticket = Ticket(
        tracker="github",
        id="#9",
        repo="acme/shop",
        steps=(TicketStep(act="assigned", at=clock.now(), login="octo-cat"),),
    )

    def assigned(record: Record) -> Record:
        return replace(record, task=replace(record.task, ticket=ticket))

    tasks.update(state, SLUG, assigned, tasks.read(state, SLUG).revision)
    tripped(capsys, world)
    drop(capsys, world)
    run_git(world.checkout, "branch", f"{BRANCH}-2", "main")
    assert refused(capsys, world, "task", "resume", SLUG)["code"] == "branch-taken"
    dropped = tasks.read(state, SLUG).task
    assert dropped.ticket == ticket
    assert set(tickets.owed(dropped, None)) == {"dropped", "unassigned"}
    assert not places.task_folder(state, f"{SLUG}-2").exists()
    blocked = refused(
        capsys,
        world,
        *opening,
        "other-task",
        "--ask",
        "another",
        "--ticket",
        "9",
        *repo,
    )
    assert blocked["code"] == "ticket-owed"
