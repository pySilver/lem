"""A feature in parts on a real repository and `LocalForge`: each part is cut from the feature's
branch, its pull request goes into that branch, and it merges and cleans there, while the base
keeps none of it (`docs/plans/2026-11-27-a-feature-in-parts.md`, step 36a).

The feature's record and its branch on origin stand in for the split of step 36b: the test
writes the record `queued` on `feature/x` and pushes that branch, as the split will. Every other
step is a command of the tree, run in this process with `--repo` to the test's repository, with
the ports of `tests/journeys/test_skeleton.py` (real git and `LocalForge`).

A second part, which the owner approved, meets the first part's merge into the feature's branch:
his merge is refused for the moved base, its checks run on the part rebased onto the branch as
it is now, and the server's merge of his standing approval lands it.
"""

import json
from functools import partial
from typing import TYPE_CHECKING, cast

import pytest
from msgspec.structs import replace

from fakes.forge import LocalForge
from fakes.harness import FakeHarness
from fakes.outside import FakeJudge, FakeTracker, RecordingNotifier
from fakes.repo import RealRepo, git_env, run_git
from fakes.terminal import FakeTerminal
from journeys.test_skeleton import (
    CRITERIA,
    NO_TEST,
    REVIEW,
    Acts,
    Counted,
    Envelope,
    World,
    lem,
    observed,
)
from lem.adapters import git_cli
from lem.app import wiring
from lem.ports.place import Place
from lem.store import tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.ports.forge import Forge
    from lem.ports.git import Git
    from lem.records.record import Record

type Capsys = pytest.CaptureFixture[str]

FEATURE = "x"
FEATURE_BRANCH = "feature/x"
FIRST, SECOND = "readme-says-receive", "notes-say-hello"
SETTINGS = b"""[branch]
base = "main"
land = "agent"
history = "squash"

[checks]
commands = ["test -f README.md"]
"""


def made(folder: Path, monkeypatch: pytest.MonkeyPatch) -> World:
    """A repository with Lem's settings on `main`, its forge, and the ports bound to them."""
    files = {"README.md": b"The README says recieve.\n", ".lem/settings.toml": SETTINGS}
    repo = RealRepo.init(folder / "repo", files)
    acts = Acts()
    world = World(repo=repo, forge=LocalForge(remote=repo), acts=acts, folder=folder)
    place = Place(checkout=repo.checkout, home=folder / "home", environ=git_env())
    ports = wiring.Ports(
        git=cast("Git", Counted(git_cli.bind(place), acts)),
        forge=cast("Forge", Counted(world.forge, acts)),
        terminal=FakeTerminal(),
        harness=FakeHarness(),
        tracker=FakeTracker(),
        notifier=RecordingNotifier(),
        judge=FakeJudge(),
    )
    monkeypatch.setattr(wiring, "bound", lambda place: ports)
    observed(monkeypatch, acts)
    monkeypatch.chdir(folder)
    return world


def ok(capsys: Capsys, world: World, *argv: str, inside: str | None = None) -> Envelope:
    """`lem ARGV` in the main checkout, or in the worktree of the task `inside`; it holds."""
    where = worktree(world, inside) if inside else world.checkout
    envelope = lem(capsys, where, *argv)
    assert envelope["ok"] is True, envelope
    return envelope


def worktree(world: World, slug: str) -> Path:
    return world.checkout / ".lem" / "worktrees" / slug


def folder_of(world: World, slug: str) -> Path:
    return world.checkout / ".lem" / "state" / "tasks" / slug


def record_of(world: World, slug: str) -> Envelope:
    return json.loads((folder_of(world, slug) / "task.json").read_text())


def queued(before: Record) -> Record:
    """The feature as the split of step 36b leaves it: queued, on its branch."""
    task = replace(before.task, status="queued", branch=FEATURE_BRANCH)
    return replace(before, task=task)


def feature(capsys: Capsys, world: World) -> None:
    """The feature `x`: its record queued on `feature/x`, and that branch on origin with one
    commit of its own."""
    ok(capsys, world, "task", "open", FEATURE, "--ask", "the docs, in two parts")
    state = world.checkout / ".lem" / "state"
    revision = tasks.read(state, FEATURE).revision
    tasks.update(state, FEATURE, queued, revision)
    world.repo.outside_commit(FEATURE_BRANCH, {"FEATURE.md": b"the feature\n"})


def shaped(
    capsys: Capsys, world: World, slug: str, ask: str, part_of: str | None = FEATURE
) -> None:
    """A part of `x`, or with no `part_of` a task of its own, opened, read, its criterion
    approved, and its worktree made."""
    joins = ("--part-of", part_of) if part_of else ()
    ok(capsys, world, "task", "open", slug, "--ask", ask, *joins)
    words = ("--type", "docs", "--why", "a line of the docs", "--track", "small")
    ok(capsys, world, "task", "read", slug, *words, "--then", "fast")
    (folder_of(world, slug) / "criteria.md").write_text(CRITERIA)
    ok(capsys, world, "criteria", "approve", slug, "--small")
    ok(capsys, world, "task", "worktree", slug)


def built(capsys: Capsys, world: World, slug: str, files: dict[str, str]) -> None:
    """The builder's change on the part's branch, and the part made ready."""
    ok(capsys, world, "task", "move", slug, "building", "--line", "one builder")
    tree = worktree(world, slug)
    for name, body in files.items():
        (tree / name).write_text(body)
    run_git(tree, "add", "--all")
    run_git(tree, "commit", "--quiet", "--message", f"docs: {slug}")
    with (folder_of(world, slug) / "criteria.md").open("a") as found:
        found.write(NO_TEST)
    ok(capsys, world, "criteria", "record", slug, inside=slug)
    ok(capsys, world, "task", "move", slug, "ready", "--line", "built", inside=slug)


def proposed(capsys: Capsys, world: World, slug: str) -> Envelope:
    """The landing from its start to its pull request."""
    for verb in ("start", "base", "checks"):
        ok(capsys, world, "land", verb, slug)
    told = ok(capsys, world, "land", "read", slug)["result"]
    said = {**REVIEW, "attempt": told["attempt"], "tip": told["tip"]}
    ok(
        capsys,
        world,
        "land",
        "read",
        slug,
        "--record",
        world.written("review.json", said),
    )
    ok(capsys, world, "land", "file", slug)
    notes = world.written("notes.md", "none\n")
    title = ("--title", f"docs: {slug}", "--notes", notes)
    return ok(capsys, world, "land", "propose", slug, *title)


def reviewed(capsys: Capsys, world: World, slug: str) -> None:
    """The merge agent's brief and its reply that says merge."""
    told = ok(capsys, world, "land", "merge-review", slug)["result"]
    said = world.written("reply.md", "Verdict: merge\n\nOne line; the checks hold.\n")
    pinned = ("--tip", told["tip"], "--base", told["base"])
    words = ("--file", said, *pinned, "--dispatch", str(told["dispatch"]))
    ok(capsys, world, "land", "merge-review", slug, *words)


def landed(capsys: Capsys, world: World, slug: str) -> None:
    for verb in ("merged", "clean"):
        ok(capsys, world, "land", verb, slug)
    found = record_of(world, slug)
    assert (found["task"]["status"], found["landing"]["phase"]) == ("landed", "ended")


def test_two_parts_land_into_the_features_branch_and_the_second_is_checked_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    base = world.repo.head_of("main")
    feature(capsys, world)
    shaped(capsys, world, FIRST, "the README says recieve; fix it")
    shaped(capsys, world, SECOND, "the notes say hello")
    assert record_of(world, FEATURE)["task"]["after"] == [FIRST, SECOND]
    # each part is cut from the feature's branch, not from main
    assert (worktree(world, FIRST) / "FEATURE.md").is_file()
    assert (worktree(world, SECOND) / "FEATURE.md").is_file()

    built(capsys, world, SECOND, {"NOTES.md": "Hello.\n"})
    assert proposed(capsys, world, SECOND)["result"]["green"] is True
    reviewed(capsys, world, SECOND)
    tip = record_of(world, SECOND)["landing"]["proposed"]["tip"]

    built(capsys, world, FIRST, {"README.md": "The README says receive.\n"})
    assert record_of(world, FIRST)["landing"] is None
    proposed(capsys, world, FIRST)
    assert record_of(world, FIRST)["landing"]["started"]["base_ref"] == FEATURE_BRANCH
    reviewed(capsys, world, FIRST)
    ok(
        capsys,
        world,
        "land",
        "merge",
        FIRST,
        "--by",
        "merger",
        "--message",
        "docs: one",
    )
    landed(capsys, world, FIRST)
    assert not worktree(world, FIRST).exists()
    moved = world.repo.head_of(FEATURE_BRANCH)
    assert moved is not None

    # the owner's approval of the second part meets the first part's merge
    owner = ("--by", "owner", "--tip", tip, "--message", "docs: two")
    refused = lem(capsys, world.checkout, "land", "merge", SECOND, *owner)
    assert refused["refusal"]["code"] == "base", refused
    assert record_of(world, SECOND)["landing"]["standing"]["by_act"] == "session"
    for verb in ("start", "base", "checks"):
        ok(capsys, world, "land", verb, SECOND)
    checked = record_of(world, SECOND)["landing"]["checked"]
    assert checked["base"] == moved
    assert (
        run_git(worktree(world, SECOND), "merge-base", "--is-ancestor", moved, "HEAD")
        == ""
    )
    assert (
        worktree(world, SECOND) / "README.md"
    ).read_text() == "The README says receive.\n"
    title = (
        "--title",
        f"docs: {SECOND}",
        "--notes",
        world.written("notes.md", "none\n"),
    )
    ok(capsys, world, "land", "propose", SECOND, *title)
    standing = (
        "--by",
        "owner",
        "--via",
        "server",
        "--standing",
        "--message",
        "docs: two",
    )
    ok(capsys, world, "land", "merge", SECOND, *standing)
    landed(capsys, world, SECOND)

    pulls = world.forge.pulls
    assert [(pull.base, pull.state) for pull in pulls.values()] == [
        (FEATURE_BRANCH, "merged"),
        (FEATURE_BRANCH, "merged"),
    ]
    assert [number for number, _ in world.forge.merge_calls] == [2, 1]
    on_feature = partial(run_git, world.repo.origin, "show")
    assert on_feature(f"{FEATURE_BRANCH}:README.md") == "The README says receive."
    assert on_feature(f"{FEATURE_BRANCH}:NOTES.md") == "Hello."
    # nothing reached the base, and the feature still waits for its end
    assert on_feature("main:README.md") == "The README says recieve."
    assert world.repo.head_of("main") == base
    feature_task = record_of(world, FEATURE)["task"]
    assert (feature_task["status"], feature_task["after"]) == (
        "queued",
        [FIRST, SECOND],
    )
    for slug in (FIRST, SECOND):
        assert world.repo.head_of(f"docs/{slug}") is None


def test_a_dropped_part_cleans_after_its_feature_was_dropped_too(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    ok(capsys, world, "task", "open", "first", "--ask", "a task the feature waits for")
    ask = ("--ask", "the docs, in parts", "--after", "first")
    ok(capsys, world, "task", "open", FEATURE, *ask)
    ok(capsys, world, "task", "worktree", FEATURE, "--branch", FEATURE_BRANCH)
    run_git(worktree(world, FEATURE), "push", "--quiet", "origin", FEATURE_BRANCH)
    ok(capsys, world, "task", "open", FIRST, "--ask", "a part", "--part-of", FEATURE)
    ok(capsys, world, "task", "worktree", FIRST, "--branch", f"docs/{FIRST}")
    for slug in (FIRST, FEATURE):
        line = ("--line", "the owner drops it")
        ok(capsys, world, "task", "move", slug, "dropped", *line)
    cleaned = ok(capsys, world, "land", "clean", FIRST)["result"]
    assert cleaned["branch_gone"] is True, cleaned
    assert not worktree(world, FIRST).exists()
    assert record_of(world, FIRST)["task"]["status"] == "dropped"


SPLIT = """## Acceptance criteria

Size: full, because the README and the notes change, in three parts.

### readme-says-receive: the README says receive

1. The README says receive, not recieve.

### notes-say-hello: the notes say hello

2. The notes say hello.

### changes-say-two: the changes name both (independent)

3. The changes name the README and the notes.

### The whole feature

4. The README and the notes agree.
"""
THREE = (FIRST, SECOND, "changes-say-two")


def approved_feature(capsys: Capsys, world: World, *ticket: str) -> str:
    """The feature `x`, shaping, from the ticket `ticket` names when it names one, its
    criteria read by the personas and approved by the owner; the path of its criteria."""
    ask = ("--ask", "the docs, in three parts", *ticket)
    ok(capsys, world, "task", "open", FEATURE, *ask)
    words = ("--type", "docs", "--why", "the docs", "--track", "full")
    ok(capsys, world, "task", "read", FEATURE, *words, "--then", "interview")
    path = world.written("criteria.md", SPLIT)
    told = ok(capsys, world, "criteria", "digest", FEATURE, "--file", path)
    read = ("done", "--by", "lem", "--asked", "2", "--answered", "2")
    families = ("--family", "opus", "--family", "sol", "--criteria", "4")
    marked = ("--flagged", "0", "--digest", told["result"]["digest"])
    ok(capsys, world, "criteria", "read", FEATURE, *read, *families, *marked)
    ok(capsys, world, "criteria", "approve", FEATURE, "--file", path)
    return path


def test_a_split_of_three_headings_ends_with_three_parts_and_the_feature_queued(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    base = world.repo.head_of("main")
    assert base is not None
    path = approved_feature(capsys, world)
    done = ok(capsys, world, "task", "split", FEATURE, "--file", path)["result"]
    assert [(part["slug"], part.get("after", [])) for part in done["parts"]] == [
        (FIRST, []),
        (SECOND, [FIRST]),
        ("changes-say-two", []),
    ]
    assert done["starts"] == [FIRST, "changes-say-two"]
    # feature/x is on origin, cut from main, and the feature waits for its three parts
    assert world.repo.head_of(FEATURE_BRANCH) == base
    feature_task = record_of(world, FEATURE)["task"]
    assert (feature_task["status"], feature_task["after"]) == ("queued", list(THREE))
    assert feature_task["shape"]["then"] == "lead"
    for slug in THREE:
        part = record_of(world, slug)["task"]
        assert part["part_of"] == FEATURE
        assert len(part["criteria"]["approvals"]) == 1
    # a second run makes nothing
    again = ok(capsys, world, "task", "split", FEATURE, "--file", path)["result"]
    assert [part.get("made", False) for part in again["parts"]] == [False] * 3
    # the first part is cut from the feature's branch
    ok(capsys, world, "task", "worktree", FIRST)
    assert record_of(world, FIRST)["task"]["branch"] == f"docs/{FIRST}"
    assert (
        run_git(worktree(world, FIRST), "merge-base", "--is-ancestor", base, "HEAD")
        == ""
    )
    assert world.repo.head_of(f"docs/{FIRST}") is None
