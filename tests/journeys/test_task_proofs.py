"""A task's worktree and claims on a throwaway repository."""

import json
import os
import subprocess
import sys
from pathlib import Path
from shutil import copy2
from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from fakes.command import lem
from fakes.repo import RealRepo, git_env, run_git
from journeys.agent import BUILDING, ok, refused, through
from journeys.test_park_drop import drop, tripped
from journeys.test_skeleton import BRANCH, SLUG, made
from journeys.test_standard_track import (
    CRITERIA,
    NOTES,
    ROUND,
    TASKS,
    TESTS,
    TITLE,
    built,
    commit,
    planned,
    started,
)
from lem.board.views.activity import happenings
from lem.kernel import clock, paths
from lem.model.task import tickets
from lem.records.journal.task import StateNoted
from lem.records.tickets import Ticket, TicketStep
from lem.store import places, tasks

if TYPE_CHECKING:
    from journeys.test_skeleton import Envelope, World
    from lem.records.record import Record

type Capsys = pytest.CaptureFixture[str]


def copy_tracked(source: Path, target: Path) -> None:
    """Copy the tracked paths from disk, with their local edits and symbolic links."""
    names = subprocess.check_output(
        ["git", "ls-files", "-z"], cwd=source, env=git_env()
    )
    for name in filter(None, names.split(b"\0")):
        relative = Path(os.fsdecode(name))
        path = target / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        copy2(source / relative, path, follow_symlinks=False)


def test_the_setup_source_includes_a_local_edit_to_a_tracked_file(
    tmp_path: Path,
) -> None:
    path = ".lem/settings.toml"
    before = b'[checks]\nsetup = ["true"]\n'
    edited = b'[checks]\nsetup = ["exit 13"]\n'
    repo = RealRepo.init(tmp_path / "original", {path: before})
    (repo.checkout / path).write_bytes(edited)
    (repo.checkout / "untracked").touch()
    target = tmp_path / "snapshot"
    copy_tracked(repo.checkout, target)
    assert (target / path).read_bytes() == edited
    assert not (target / "untracked").exists()


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
    copy_tracked(paths.root(), checkout)
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


def test_a_move_from_a_worktree_keeps_its_branch_and_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    slug = "invoice"
    branch = f"fix/{slug}"
    ok(capsys, world, "task", "open", slug, "--ask", "keep 0123 as a string")
    state = world.checkout / places.STATE
    assert tasks.read(state, slug).task.branch is None
    tree = world.checkout / ".lem" / "worktrees" / slug
    run_git(world.checkout, "worktree", "add", "-b", branch, str(tree), "main")
    subject = "fix: 0123 is a string"
    run_git(tree, "commit", "--allow-empty", "-m", subject)
    tip = run_git(tree, "rev-parse", "HEAD")
    ok(
        capsys,
        world,
        "task",
        "move",
        slug,
        "building",
        "--line",
        "one builder",
        at=tree,
    )
    run_git(tree, "commit", "--allow-empty", "-m", "fix: keep the leading zero")
    record = tasks.read(state, slug)
    assert record.task.status == "building"
    assert record.task.branch == branch
    move = record.journal[-1]
    assert isinstance(move, StateNoted)
    assert (move.branch, move.head, move.subject) == (branch, tip, subject)


def before_resume(capsys: Capsys, world: World, *, skipped: bool) -> None:
    ok(capsys, world, "task", "open", SLUG, "--ask", "fix the README")
    ok(
        capsys,
        world,
        "task",
        "read",
        SLUG,
        "--type",
        "docs",
        "--why",
        "a word",
        "--track",
        "full",
        "--then",
        "interview",
    )
    sheet = world.written("criteria.md", CRITERIA)
    if skipped:
        ok(capsys, world, "criteria", "skip", SLUG, "asked")
        ok(capsys, world, "criteria", "skip", SLUG, "yes")
    else:
        mark = ok(capsys, world, "criteria", "digest", SLUG, "--file", sheet)
        ok(
            capsys,
            world,
            "criteria",
            "read",
            SLUG,
            "done",
            "--by",
            "lem",
            "--asked",
            "2",
            "--answered",
            "2",
            "--family",
            "opus",
            "--criteria",
            "1",
            "--flagged",
            "1",
            "--digest",
            mark["result"]["digest"],
        )
    ok(
        capsys,
        world,
        "decisions",
        "log",
        SLUG,
        "--by",
        "owner",
        "--what",
        "Where",
        "--chose",
        "the first line",
        "--why",
        "a reader sees it at once",
    )
    ok(capsys, world, "criteria", "approve", SLUG, "--file", sheet)
    started(capsys, world)
    plan = planned(capsys, world, start=False)
    ok(capsys, world, "task", "build", plan)
    commit(
        world,
        {
            "README.md": "The README says receive.\n",
            "tests/receive.sh": "grep -q receive README.md\n",
        },
        TITLE,
    )
    tripped(capsys, world)
    drop(capsys, world)


def help_breaker(capsys: Capsys, world: World, slug: str, breaker: int) -> None:
    ok(
        capsys,
        world,
        "decisions",
        "log",
        slug,
        "--by",
        "owner",
        "--breaker",
        str(breaker),
        "--words",
        "use the first line",
        "--what",
        "Where the word goes",
        "--chose",
        "the first line",
        "--why",
        "a reader sees it at once",
    )
    ok(capsys, world, "task", "move", slug, "ready", "--line", "built")


def propose_built(capsys: Capsys, world: World, slug: str) -> Envelope:
    for verb in ("start", "base", "polish"):
        ok(capsys, world, "land", verb, slug)
    ok(capsys, world, "land", "polish", slug, "--done")
    ok(capsys, world, "land", "checks", slug)
    brief = ok(capsys, world, "land", "read", slug)["result"]
    review = {**ROUND, "attempt": brief["attempt"], "tip": brief["tip"]}
    ok(
        capsys,
        world,
        "land",
        "read",
        slug,
        "--record",
        world.written("read.json", review),
    )
    return ok(
        capsys,
        world,
        "land",
        "propose",
        slug,
        "--title",
        TITLE,
        "--notes",
        world.written("notes.md", NOTES),
    )


@pytest.mark.parametrize("skipped", [False, True], ids=["flagged", "skipped"])
def test_the_successor_keeps_activity_and_proposes_after_the_owners_help(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys, *, skipped: bool
) -> None:
    world = made(tmp_path, monkeypatch)
    before_resume(capsys, world, skipped=skipped)
    state = world.checkout / places.STATE
    old = tasks.read(state, SLUG)
    resumed = ok(capsys, world, "task", "resume", SLUG)["result"]
    slug = resumed["task"]
    successor = tasks.read(state, slug)
    assert successor.task.criteria == old.task.criteria
    help_breaker(capsys, world, slug, resumed["breaker"])
    assert propose_built(capsys, world, slug)["result"]["pull"]["number"] == 1
    assert tasks.read(state, slug).task.status == "open"

    copied = tuple(happenings.by_entry(successor))
    names = tuple(row.told.head for row in copied)
    first = (
        "You said to skip the personas’ read"
        if skipped
        else "The personas read the criteria"
    )
    decision = names.index("Decision 1, by you")
    approved = names.index("You approved the criteria")
    stopped = next(i for i, name in enumerate(names) if name.startswith("The build of"))
    assert names.index(first) < decision < approved < stopped
    for row in copied:
        assert row.at == successor.task.opened
        assert f"carried over from {SLUG}" in row.told.sub


def test_a_clear_lead_read_proposes_green_after_a_refused_edit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: Capsys,
) -> None:
    world = made(tmp_path, monkeypatch)
    ok(capsys, world, "task", "open", SLUG, "--ask", "fix the README")
    ok(capsys, world, "task", "span", SLUG, "scout", "start")
    ok(capsys, world, "task", "span", SLUG, "scout", "end")
    ok(
        capsys,
        world,
        "task",
        "read",
        SLUG,
        "--type",
        "docs",
        "--why",
        "a word",
        "--track",
        "full",
        "--then",
        "lead",
    )
    started(capsys, world)
    plan = ok(capsys, world, "task", "plan-file", SLUG)["result"]["path"]
    commit(world, {plan: CRITERIA + TESTS + TASKS}, "docs: the plan")
    mark = ok(capsys, world, "criteria", "digest", SLUG)["result"]["digest"]
    ok(
        capsys,
        world,
        "criteria",
        "read",
        SLUG,
        "done",
        "--by",
        "lead",
        "--asked",
        "2",
        "--answered",
        "2",
        "--family",
        "opus",
        "--criteria",
        "1",
        "--flagged",
        "0",
        "--digest",
        mark,
    )
    frozen = ok(capsys, world, "criteria", "approve", SLUG, "--read")["result"]
    assert (frozen["by"], frozen["digest"]) == ("read", mark)
    wrong = refused(
        capsys,
        world,
        "decisions",
        "criterion",
        SLUG,
        "--changed",
        "1",
        "--was",
        "Not the criterion.",
        "--now",
        "x",
        "--why",
        "w",
        "--by",
        "lead",
    )
    assert "after every earlier change" in wrong["why"]
    ok(capsys, world, "criteria", "record", SLUG)
    ok(capsys, world, "task", "planned", SLUG, "--tasks", "1")
    built(capsys, world, plan)

    proposal = propose_built(capsys, world, SLUG)["result"]
    assert proposal["green"] is True
    body = world.forge.bodies[proposal["pull"]["number"]]
    assert body.startswith("**Green.**")
    assert "the change was not read" not in body
    assert (
        "one model family (opus); nobody confused; the build started with no wait"
        in body
    )
    assert "the criteria were written from the scout's facts of the code" in body
    assert str(world.checkout) not in body


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
