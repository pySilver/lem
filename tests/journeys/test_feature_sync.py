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

import pytest

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
from journeys.test_skeleton import Killed, lem
from lem.app.sessions import acts, log
from lem.app.tasks import sync_checks
from lem.board.duties import context, sync
from lem.board.duties.context import Duty
from lem.board.duties.memory import Kept
from lem.kernel import clock
from lem.ports.terminal import Pane
from lem.store import places, tasks

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from journeys.test_feature_parts import Capsys
    from journeys.test_skeleton import World
    from lem.app.tasks.sync_frame import Sync
    from lem.records.landing.checks import Outcome

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

    # a builder resolves the conflict and commits the merge, and a part merges meanwhile:
    # the resolution, which carries the sync's subject, is a builder's and stays
    tree = worktree(world, FEATURE)
    (tree / "README.md").write_text("The feature and main say receive.\n")
    run_git(tree, "add", "--all")
    run_git(tree, "commit", "--quiet", "--no-edit")
    resolved = run_git(tree, "rev-parse", "HEAD")
    parents = run_git(tree, "rev-list", "--parents", "-n", "1", resolved)
    assert parents.split()[1:] == [before, base]
    part = world.repo.outside_commit(FEATURE_BRANCH, {"NOTES.md": b"Hello.\n"})
    apart = lem(capsys, world.checkout, "task", "sync", FEATURE)
    assert apart["refusal"]["code"] == "diverged", apart
    assert run_git(tree, "rev-parse", "HEAD") == resolved

    run_git(tree, "merge", "--quiet", "--no-edit", f"origin/{FEATURE_BRANCH}")
    synced = ok(capsys, world, "task", "sync", FEATURE)["result"]
    assert (synced["pushed"], synced["before"], synced["merge"]) == (True, part, None)
    assert world.repo.head_of(FEATURE_BRANCH) == synced["head"]
    on_origin = run_git(world.repo.origin, "show", f"{FEATURE_BRANCH}:README.md")
    assert on_origin == "The feature and main say receive."


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


def after_checks(
    monkeypatch: pytest.MonkeyPatch, act: Callable[[int], None]
) -> list[int]:
    """Each run of the sync's checks, counted, with `act` after each, given its number: what
    happens between the checks and the push."""
    real = sync_checks.checked
    runs: list[int] = []

    def checked(sync: Sync) -> tuple[Outcome, ...]:
        outcomes = real(sync)
        runs.append(len(runs) + 1)
        act(runs[-1])
        return outcomes

    monkeypatch.setattr(sync_checks, "checked", checked)
    return runs


def behind_main(capsys: Capsys, world: World) -> str:
    """The feature `x` with one part open, and a teammate's commit on origin's `main` that
    its branch lacks; that commit."""
    started(capsys, world, {"FEATURE.md": "The feature.\n"})
    ok(capsys, world, "task", "open", PART, "--ask", "a part", "--part-of", FEATURE)
    return world.repo.outside_commit("main", {"MAIN.md": b"Main.\n"})


def part_merged(world: World, number: int) -> None:
    """A part's merge into the feature's branch on origin, as GitHub makes it."""
    world.repo.outside_commit(FEATURE_BRANCH, {f"PART-{number}.md": b"part\n"})


def test_a_part_merged_under_the_push_takes_the_merge_back_and_the_sync_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    base = behind_main(capsys, world)

    def once(number: int) -> None:
        if number == 1:
            part_merged(world, 1)

    runs = after_checks(monkeypatch, once)

    synced = ok(capsys, world, "task", "sync", FEATURE)["result"]
    assert runs == [1, 2]
    moved = world.repo.head_of(FEATURE_BRANCH)
    assert moved is not None
    assert moved == synced["head"] == synced["merge"]
    parents = run_git(world.repo.origin, "rev-list", "--parents", "-n", "1", moved)
    first = parents.split()[1]
    assert parents.split()[2:] == [base]
    assert run_git(world.repo.origin, "show", f"{first}:PART-1.md") == "part"
    assert synced["before"] == first
    assert run_git(worktree(world, FEATURE), "rev-parse", "HEAD") == moved


def test_a_branch_that_moves_under_every_push_ends_the_sync_after_its_tries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    behind_main(capsys, world)
    runs = after_checks(monkeypatch, lambda number: part_merged(world, number))

    ended = lem(capsys, world.checkout, "task", "sync", FEATURE)
    assert ended["refusal"]["code"] == "lease", ended
    assert runs == [1, 2, 3]
    third = run_git(world.repo.origin, "rev-parse", f"{FEATURE_BRANCH}^")
    tree = worktree(world, FEATURE)
    # each try took its own merge back: the worktree is where the third try began
    assert run_git(tree, "rev-parse", "HEAD") == third
    assert run_git(tree, "status", "--porcelain") == ""


def test_a_push_git_refuses_for_another_reason_ends_the_sync_at_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    behind_main(capsys, world)
    before = world.repo.head_of(FEATURE_BRANCH)
    hook = world.checkout / ".git" / "hooks" / "pre-push"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/bin/sh\necho 'pushes wait for review' >&2\nexit 1\n")
    hook.chmod(0o755)
    runs = after_checks(monkeypatch, lambda _number: None)

    refused = lem(capsys, world.checkout, "task", "sync", FEATURE)
    assert refused["refusal"]["code"] == "git", refused
    assert "push" in refused["refusal"]["why"]
    assert runs == [1]
    assert world.repo.head_of(FEATURE_BRANCH) == before


def test_a_sync_cut_before_its_push_drops_its_own_merge_once_a_part_merged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    base = behind_main(capsys, world)
    tree = worktree(world, FEATURE)

    def cut(number: int) -> None:
        if number == 1:
            raise Killed("push")

    after_checks(monkeypatch, cut)
    with pytest.raises(Killed):
        lem(capsys, world.checkout, "task", "sync", FEATURE)
    lost = run_git(tree, "rev-parse", "HEAD")
    assert lost != world.repo.head_of(FEATURE_BRANCH)
    part_merged(world, 1)

    synced = ok(capsys, world, "task", "sync", FEATURE)["result"]
    moved = world.repo.head_of(FEATURE_BRANCH)
    assert moved is not None
    assert (synced["pushed"], synced["head"]) == (True, moved)
    parents = run_git(world.repo.origin, "rev-list", "--parents", "-n", "1", moved)
    assert parents.split()[2:] == [base]
    assert parents.split()[1] == synced["before"] != lost
    listed = run_git(world.repo.origin, "rev-list", moved)
    assert lost not in listed.split()
