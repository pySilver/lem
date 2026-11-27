"""The sync of a feature on a real repository and `LocalForge` (`docs/plans/2026-11-27-a-feature-
in-parts.md`, step 36c): a task lands on `main`, the board server's sync duty wakes the feature's
session, `lem task sync x` merges origin's `main` into `feature/x` by a merge commit, checks it
and pushes it, and a part that the owner approved meets the moved feature branch: his merge is
refused `base`, and its checks run on the part rebased onto the synced branch. A sync whose
merge conflicts stops with its files and pushes nothing, and once a builder committed the
resolution, the sync runs again and pushes it.

The helpers and the ports are those of `test_feature_parts.py` (real git, `LocalForge`, every
step a command of the tree in this process). The duty runs as the server's runner runs it, with
the ports of the test and the fake terminal.
"""

import os
from typing import TYPE_CHECKING

from fakes.repo import run_git
from fakes.terminal import FakeTerminal
from journeys.test_feature_parts import (
    FEATURE,
    FEATURE_BRANCH,
    built,
    folder_of,
    landed,
    made,
    ok,
    proposed,
    queued,
    record_of,
    reviewed,
    shaped,
    worktree,
)
from journeys.test_skeleton import lem
from lem.app.sessions import acts, log
from lem.board.duties import context, sync
from lem.board.duties.context import Duty
from lem.board.duties.memory import Kept
from lem.kernel import clock
from lem.ports.terminal import Pane
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

    from journeys.test_feature_parts import Capsys
    from journeys.test_skeleton import World

PART = "notes-say-hello"
ON_MAIN = "main-has-notes"


def started(capsys: Capsys, world: World, files: dict[str, str]) -> None:
    """The feature `x` with its worktree on `feature/x`, one commit of `files` of its own
    pushed to origin, and its record queued, as the split of step 36b leaves it."""
    ok(capsys, world, "task", "open", FEATURE, "--ask", "the docs, in parts")
    ok(capsys, world, "task", "worktree", FEATURE, "--branch", FEATURE_BRANCH)
    tree = worktree(world, FEATURE)
    for name, body in files.items():
        (tree / name).write_text(body)
    run_git(tree, "add", "--all")
    run_git(tree, "commit", "--quiet", "--message", "docs: the feature starts")
    run_git(tree, "push", "--quiet", "origin", FEATURE_BRANCH)
    state = world.checkout / ".lem" / "state"
    tasks.update(state, FEATURE, queued, tasks.read(state, FEATURE).revision)


def in_agterm(world: World, slug: str) -> None:
    """The task's own session, live in a workspace of agterm, on record: the workspace a new
    session of the feature opens in."""
    terminal = duty_of(world).here.ports.terminal
    assert isinstance(terminal, FakeTerminal)
    pane = Pane(id="S-PART", name=slug, workspace="W-1")
    terminal.panes[pane.id] = pane
    opened = acts.Open(
        at=clock.now(),
        session=pane.id,
        name=slug,
        phase="fast",
        why="new",
        workspace="W-1",
    )
    log.append(folder_of(world, slug), opened)


def duty_of(world: World) -> Duty:
    """The duty of the test's workspace now, as the server's runner binds it."""
    space = places.workspace(world.checkout)
    here = context.bound(space, os.environ, world.folder / "home")
    return Duty(name="repo", here=here, now=clock.now(), kept=Kept())


def syncs(world: World) -> list[str | None]:
    """The head of each `sync` wake of the feature's session, in order."""
    found = log.read(folder_of(world, FEATURE))
    woken = (act for act in found if isinstance(act, acts.Wake))
    return [act.head for act in woken if act.why == "sync"]


def lands_on_main(capsys: Capsys, world: World) -> str:
    """A task of its own lands on `main`; origin's `main` after it."""
    shaped(capsys, world, ON_MAIN, "the notes of main", part_of=None)
    built(capsys, world, ON_MAIN, {"MAIN.md": "Main.\n"})
    proposed(capsys, world, ON_MAIN)
    reviewed(capsys, world, ON_MAIN)
    words = ("--by", "merger", "--message", "docs: main notes")
    ok(capsys, world, "land", "merge", ON_MAIN, *words)
    landed(capsys, world, ON_MAIN)
    head = world.repo.head_of("main")
    assert head is not None
    return head


def test_a_base_merge_wakes_the_feature_whose_sync_moves_an_approved_parts_base(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    started(capsys, world, {"FEATURE.md": "The feature.\n"})
    shaped(capsys, world, PART, "the notes say hello")
    built(capsys, world, PART, {"NOTES.md": "Hello.\n"})
    assert proposed(capsys, world, PART)["result"]["green"] is True
    reviewed(capsys, world, PART)
    tip = record_of(world, PART)["landing"]["proposed"]["tip"]
    in_agterm(world, PART)
    sync.tick(duty_of(world))
    assert syncs(world) == []

    base = lands_on_main(capsys, world)
    sync.tick(duty_of(world))
    sync.tick(duty_of(world))
    assert syncs(world) == [base]
    # no session of the feature lived: the wake opened one beside the part's
    opened = log.newest_open(log.read(folder_of(world, FEATURE)))
    assert opened is not None
    assert (opened.why, opened.workspace) == ("sync", "W-1")

    before = world.repo.head_of(FEATURE_BRANCH)
    done = ok(capsys, world, "task", "sync", FEATURE)
    synced = done["result"]
    assert (synced["pushed"], synced["base_commit"], synced["before"]) == (
        True,
        base,
        before,
    )
    assert [one["command"] for one in synced["checks"]] == ["test -f README.md"]
    head = world.repo.head_of(FEATURE_BRANCH)
    assert head is not None
    assert head == synced["head"] == synced["merge"]
    parents = run_git(world.repo.origin, "rev-list", "--parents", "-n", "1", head)
    assert parents.split()[1:] == [before, base]
    on_feature = run_git(world.repo.origin, "show", f"{FEATURE_BRANCH}:MAIN.md")
    assert on_feature == "Main."
    assert done["say"] == (
        f"{FEATURE_BRANCH} took in origin/main, and origin has it at {head[:7]}"
    )
    # the branch holds the base now: no wake, and a sync again takes in nothing
    sync.tick(duty_of(world))
    assert syncs(world) == [base]
    again = ok(capsys, world, "task", "sync", FEATURE)["result"]
    assert (again["pushed"], again["head"]) == (False, head)

    # the owner's approval of the part meets the synced branch
    owner = ("--by", "owner", "--tip", tip, "--message", "docs: hello")
    refused = lem(capsys, world.checkout, "land", "merge", PART, *owner)
    assert refused["refusal"]["code"] == "base", refused
    for verb in ("start", "base", "checks"):
        ok(capsys, world, "land", verb, PART)
    checked = record_of(world, PART)["landing"]["checked"]
    assert checked["base"] == head
    assert (worktree(world, PART) / "MAIN.md").read_text() == "Main.\n"
    assert record_of(world, FEATURE)["task"]["status"] == "queued"


def test_a_conflicting_sync_stops_with_its_files_and_pushes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    started(capsys, world, {"README.md": "The feature says receive.\n"})
    ok(capsys, world, "task", "open", PART, "--ask", "a part", "--part-of", FEATURE)
    base = world.repo.outside_commit("main", {"README.md": b"Main says receive.\n"})
    before = world.repo.head_of(FEATURE_BRANCH)

    stopped = lem(capsys, world.checkout, "task", "sync", FEATURE)
    refusal = stopped["refusal"]
    assert isinstance(refusal, dict)
    assert refusal["code"] == "conflict", refusal
    assert "README.md" in refusal["why"]
    assert "nothing was pushed" in refusal["why"]
    assert world.repo.head_of(FEATURE_BRANCH) == before
    again = lem(capsys, world.checkout, "task", "sync", FEATURE)
    assert again["refusal"]["code"] == "dirty", again

    # a builder resolves the conflict and commits the merge; the sync pushes it
    tree = worktree(world, FEATURE)
    (tree / "README.md").write_text("The feature and main say receive.\n")
    run_git(tree, "add", "--all")
    run_git(tree, "commit", "--quiet", "--no-edit")
    resolved = run_git(tree, "rev-parse", "HEAD")
    synced = ok(capsys, world, "task", "sync", FEATURE)["result"]
    assert (synced["pushed"], synced["head"], synced["merge"]) == (True, resolved, None)
    assert world.repo.head_of(FEATURE_BRANCH) == resolved
    parents = run_git(world.repo.origin, "rev-list", "--parents", "-n", "1", resolved)
    assert parents.split()[1:] == [before, base]


def test_a_red_check_on_the_merge_pushes_nothing_until_a_builder_repairs_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    started(capsys, world, {"FEATURE.md": "The feature.\n"})
    ok(capsys, world, "task", "open", PART, "--ask", "a part", "--part-of", FEATURE)
    world.repo.outside_commit("main", {"README.md": None})
    before = world.repo.head_of(FEATURE_BRANCH)

    red = lem(capsys, world.checkout, "task", "sync", FEATURE)
    refusal = red["refusal"]
    assert isinstance(refusal, dict)
    assert refusal["code"] == "red", red
    assert "`test -f README.md`" in refusal["why"]
    assert world.repo.head_of(FEATURE_BRANCH) == before
    tree = worktree(world, FEATURE)
    merge = run_git(tree, "rev-parse", "HEAD")
    assert merge != before

    # a builder repairs the merge in the worktree; the sync checks and pushes both
    (tree / "README.md").write_text("The README is back.\n")
    run_git(tree, "add", "--all")
    run_git(tree, "commit", "--quiet", "--message", "docs: the README is back")
    synced = ok(capsys, world, "task", "sync", FEATURE)["result"]
    assert (synced["pushed"], synced["merge"]) == (True, None)
    assert world.repo.head_of(FEATURE_BRANCH) == synced["head"]
    assert run_git(world.repo.origin, "rev-parse", f"{synced['head']}^") == merge
