"""The end of a feature on a real repository and `LocalForge` (`docs/plans/2026-11-27-a-feature-
in-parts.md`, step 36d): two parts land into `feature/x`, a merge to `main` between them is
taken in by `lem task sync x`, and once the last part ended the queue duty gives the feature its
turn. Its lead's builder writes the test of the whole feature, and the landing of `x` runs with
the five differences of the end: `start` waits for no part, `base` takes in `main` by a merge
commit, no polish pass, the review's brief lists the parts and reads what no part's review read,
and the merge is the owner's alone, one squash whatever `branch.history` says, which lists the
parts. Then `clean` removes `feature/x`. A teammate's pull request into `feature/x` keeps the
merge back.

The project's `branch.history` is `keep`, so that each part lands its own commits (a rebase on
the forge) and the feature's squash is the end's own difference. The helpers are those of
`test_feature_parts.py` and `test_feature_sync.py`: real git, `LocalForge`, every step a command
of the tree in this process.
"""

import json
from typing import TYPE_CHECKING, cast

from fakes.forge import LocalForge
from fakes.harness import FakeHarness
from fakes.outside import FakeJudge, FakeTracker, RecordingNotifier
from fakes.repo import RealRepo, git_env, run_git
from fakes.terminal import FakeTerminal
from journeys.test_feature_parts import (
    FEATURE,
    FEATURE_BRANCH,
    FIRST,
    SECOND,
    built,
    folder_of,
    ok,
    proposed,
    queued,
    record_of,
    reviewed,
    shaped,
    worktree,
)
from journeys.test_feature_sync import duty_of, in_agterm
from journeys.test_skeleton import REVIEW, Acts, Counted, World, lem, observed
from lem.adapters import git_cli
from lem.app import wiring
from lem.app.sessions import acts, log
from lem.board.duties import queue
from lem.ports.place import Place
from lem.store import tasks

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

    from journeys.test_feature_parts import Capsys
    from journeys.test_skeleton import Envelope
    from lem.ports.forge import Forge
    from lem.ports.git import Git

KEEP = b"""[branch]
base = "main"
land = "agent"
history = "keep"

[checks]
commands = ["test -f README.md"]
"""
CRITERIA = """## Acceptance criteria

Size: full, because the README and the notes change together, in two parts.

1. The README and the notes agree: `sh tests/agree.sh` finds both.
"""
TASKS = "\n## Tasks\n\n1. The test that the README and the notes agree.\n"
TITLE = "docs: the README and the notes agree"
NOTES = (
    "## Decisions\n\nnone\n\n## Left open\n\nnone\n\n## Worth a look\n\nnone\n\n"
    "## Filed in the backlog\n\nnone\n\n## Not done\n\nnone\n"
)
ROUND = {
    **REVIEW,
    "kind": "round",
    "ran": [{"name": "claude", "why": "the project's one profile"}],
    "outside": [],
}


def made(folder: Path, monkeypatch: pytest.MonkeyPatch) -> World:
    """A repository whose settings keep each branch's commits, its forge, and the ports bound
    to them, as `test_feature_parts.made` binds them."""
    files = {"README.md": b"The README says recieve.\n", ".lem/settings.toml": KEEP}
    repo = RealRepo.init(folder / "repo", files)
    seen = Acts()
    world = World(repo=repo, forge=LocalForge(remote=repo), acts=seen, folder=folder)
    place = Place(checkout=repo.checkout, home=folder / "home", environ=git_env())
    ports = wiring.Ports(
        git=cast("Git", Counted(git_cli.bind(place), seen)),
        forge=cast("Forge", Counted(world.forge, seen)),
        terminal=FakeTerminal(),
        harness=FakeHarness(),
        tracker=FakeTracker(),
        notifier=RecordingNotifier(),
        judge=FakeJudge(),
    )
    monkeypatch.setattr(wiring, "bound", lambda place: ports)
    observed(monkeypatch, seen)
    monkeypatch.chdir(folder)
    return world


def commit(world: World, files: dict[str, str], subject: str) -> str:
    """A commit of `files` in the feature's worktree; its sha."""
    tree = worktree(world, FEATURE)
    for name, body in files.items():
        path = tree / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)
    run_git(tree, "add", "--all")
    run_git(tree, "commit", "--quiet", "--message", subject)
    return run_git(tree, "rev-parse", "HEAD")


def started(capsys: Capsys, world: World) -> None:
    """The feature `x` as the split leaves it: read for the standard track with its lead
    next, its criteria approved, its worktree on `feature/x` with a commit of its own on
    origin, and its record queued."""
    ok(
        capsys,
        world,
        "task",
        "open",
        FEATURE,
        "--ask",
        "the README and the notes agree",
    )
    words = ("--type", "docs", "--why", "the docs", "--track", "full")
    ok(capsys, world, "task", "read", FEATURE, *words, "--then", "lead")
    ok(capsys, world, "task", "span", FEATURE, "interview", "start")
    ok(capsys, world, "criteria", "skip", FEATURE, "asked")
    ok(capsys, world, "criteria", "skip", FEATURE, "yes")
    answered = world.written("criteria.md", CRITERIA)
    ok(capsys, world, "criteria", "approve", FEATURE, "--file", answered)
    ok(capsys, world, "task", "span", FEATURE, "interview", "end")
    ok(capsys, world, "task", "worktree", FEATURE, "--branch", FEATURE_BRANCH)
    commit(world, {"FEATURE.md": "The feature.\n"}, "docs: the feature starts")
    run_git(worktree(world, FEATURE), "push", "--quiet", "origin", FEATURE_BRANCH)
    state = world.checkout / ".lem" / "state"
    tasks.update(state, FEATURE, queued, tasks.read(state, FEATURE).revision)


def part_landed(capsys: Capsys, world: World, slug: str, files: dict[str, str]) -> None:
    """A part built, proposed, read by the merge agent, merged by it into `feature/x` and
    cleaned."""
    built(capsys, world, slug, files)
    assert proposed(capsys, world, slug)["result"]["green"] is True
    brief = json.loads((folder_of(world, slug) / told(world, slug)).read_text())
    assert "feature" not in brief
    reviewed(capsys, world, slug)
    ok(capsys, world, "land", "merge", slug, "--by", "merger")
    for verb in ("merged", "clean"):
        ok(capsys, world, "land", verb, slug)
    assert record_of(world, slug)["task"]["status"] == "landed"


def told(world: World, slug: str) -> str:
    """The path of the newest review brief in the task's folder."""
    found = sorted((folder_of(world, slug) / "reviews").glob("read-*.json"))
    return str(found[-1].relative_to(folder_of(world, slug)))


def turned(capsys: Capsys, world: World) -> None:
    """The queue duty's turn of the feature once its last part landed: its `queue` wake."""
    in_agterm(world, SECOND)
    queue.tick(duty_of(world))
    found = log.read(folder_of(world, FEATURE))
    whys = [act.why for act in found if isinstance(act, (acts.Open, acts.Wake))]
    assert whys[-1] == "queue", whys
    ok(capsys, world, "task", "may-start", FEATURE)


def ended_by_its_lead(capsys: Capsys, world: World) -> None:
    """The lead of the end: its plan, the builder's test of the whole feature, and the
    feature made ready."""
    line = ("--line", "the lead of the end")
    ok(capsys, world, "task", "move", FEATURE, "building", *line)
    ok(capsys, world, "task", "span", FEATURE, "lead", "start", "--by", "session")
    name = ok(capsys, world, "task", "plan-file", FEATURE)["result"]["path"]
    tests = "   - test: `sh tests/agree.sh` in `tests/agree.sh`\n"
    commit(world, {name: CRITERIA + tests + TASKS}, "docs: the plan of the end")
    ok(capsys, world, "criteria", "record", FEATURE, inside=FEATURE)
    ok(capsys, world, "task", "planned", FEATURE, "--tasks", "1")
    ok(capsys, world, "task", "build", name)
    agree = "grep -q receive README.md && grep -q Hello NOTES.md\n"
    commit(world, {"tests/agree.sh": agree}, "test: the README and the notes agree")
    ok(
        capsys,
        world,
        "task",
        "move",
        FEATURE,
        "ready",
        "--line",
        "built",
        inside=FEATURE,
    )


def due(capsys: Capsys, world: World) -> str:
    """The landing step `lem land next` names for the feature."""
    return str(ok(capsys, world, "land", "next", FEATURE)["result"]["step"])


def to_its_end(capsys: Capsys, world: World) -> str:
    """Two parts land into `feature/x`, with a merge to `main` and a sync between them; the
    queue gives the feature its turn and its lead builds the end. Origin's `main` once a
    teammate's commit landed there again, which the feature's `base` takes in."""
    started(capsys, world)
    shaped(capsys, world, FIRST, "the README says recieve; fix it")
    shaped(capsys, world, SECOND, "the notes say hello")
    assert record_of(world, FEATURE)["task"]["after"] == [FIRST, SECOND]
    part_landed(capsys, world, FIRST, {"README.md": "The README says receive.\n"})

    world.repo.outside_commit("main", {"MAIN.md": b"Main.\n"})
    synced = ok(capsys, world, "task", "sync", FEATURE)["result"]
    assert synced["pushed"] is True
    part_landed(capsys, world, SECOND, {"NOTES.md": "Hello.\n"})
    turned(capsys, world)
    ended_by_its_lead(capsys, world)
    return world.repo.outside_commit("main", {"LATER.md": b"Later.\n"})


def landed_to_its_proposal(capsys: Capsys, world: World, main: str) -> Envelope:
    """The feature's landing, each step the one `lem land next` names, to its pull request:
    no polish pass, `base` a merge of origin's `main`, and the brief of its review."""
    ran: list[str] = []
    while (verb := due(capsys, world)) != "read":
        assert verb in {"start", "base", "checks"}, (verb, ran)
        ok(capsys, world, "land", verb, FEATURE)
        ran.append(verb)
    assert ran == ["start", "base", "checks"]
    head = run_git(worktree(world, FEATURE), "rev-parse", "HEAD")
    parents = run_git(
        worktree(world, FEATURE), "rev-list", "--parents", "-n", "1", head
    )
    assert parents.split()[2:] == [main]
    told_now = ok(capsys, world, "land", "read", FEATURE)
    assert "prompts/feature-review.md" in told_now["next"]["why"]
    brief = told_now["result"]["brief"]
    said = {**ROUND, "attempt": brief["attempt"], "tip": brief["tip"]}
    record = world.written("review.json", said)
    ok(capsys, world, "land", "read", FEATURE, "--record", record)
    assert due(capsys, world) == "propose"
    words = ("--title", TITLE, "--notes", world.written("notes.md", NOTES))
    ok(capsys, world, "land", "propose", FEATURE, *words)
    reviewed(capsys, world, FEATURE)
    return brief


def test_a_feature_of_two_parts_ends_as_one_squash_on_main_after_its_turn(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    main = to_its_end(capsys, world)
    brief = landed_to_its_proposal(capsys, world, main)

    read = brief["feature"]
    assert [(part["slug"], part["status"]) for part in read["parts"]] == [
        (SECOND, "landed"),
        (FIRST, "landed"),
    ]
    assert all(part["pull"] and part["review"] for part in read["parts"])
    subjects = [one["subject"] for one in read["commits"]]
    assert subjects == [
        "docs: the feature starts",
        "docs: the plan of the end",
        "test: the README and the notes agree",
    ]
    syncs = read["syncs"]
    assert [sync["subject"] for sync in syncs] == [
        f"Merge origin/main into {FEATURE_BRANCH}"
    ] * 2
    # git made both merges alone: nothing beside them to read
    assert all("remerge" not in sync for sync in syncs)
    assert read["criteria"] == [
        {
            "number": 1,
            "text": "The README and the notes agree: `sh tests/agree.sh` finds both.",
        }
    ]

    pull = world.forge.pulls[3]
    assert (pull.base, pull.head_ref) == ("main", FEATURE_BRANCH)
    assert "## Parts" in pull.body
    assert f"- {FIRST}: #1" in pull.body
    assert f"- {SECOND}: #2" in pull.body

    tip = record_of(world, FEATURE)["landing"]["proposed"]["tip"]
    by_agent = ("--by", "merger", "--message", TITLE)
    agent = lem(capsys, world.checkout, "land", "merge", FEATURE, *by_agent)
    assert agent["refusal"]["code"] == "merger-rule", agent
    assert "the request is a feature" in agent["refusal"]["why"]
    owner = ("--by", "owner", "--tip", tip, "--message", TITLE)
    ok(capsys, world, "land", "merge", FEATURE, *owner)
    for verb in ("merged", "clean"):
        ok(capsys, world, "land", verb, FEATURE)
    found = record_of(world, FEATURE)
    assert (found["task"]["status"], found["landing"]["phase"]) == ("landed", "ended")

    squash = world.repo.head_of("main")
    assert squash is not None
    parents = run_git(world.repo.origin, "rev-list", "--parents", "-n", "1", squash)
    assert parents.split()[1:] == [main]
    message = run_git(world.repo.origin, "log", "-1", "--format=%B", squash)
    assert message.splitlines()[0] == TITLE
    assert "Parts:" in message
    assert f"- {FIRST}: #1" in message
    show = run_git(world.repo.origin, "show", "main:README.md")
    assert show == "The README says receive."
    assert run_git(world.repo.origin, "show", "main:NOTES.md") == "Hello."
    assert world.repo.head_of(FEATURE_BRANCH) is None
    assert not worktree(world, FEATURE).exists()


def test_the_feature_does_not_merge_while_a_teammates_pull_request_goes_into_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    main = to_its_end(capsys, world)
    landed_to_its_proposal(capsys, world, main)
    head = world.repo.outside_commit(
        "docs/teammate", {"TEAM.md": b"Team.\n"}, start=FEATURE_BRANCH
    )
    theirs = world.forge.open_pull(
        "docs/teammate", FEATURE_BRANCH, "docs: the team", "a teammate's part"
    )
    assert theirs.head == head

    tip = record_of(world, FEATURE)["landing"]["proposed"]["tip"]
    owner = ("--by", "owner", "--tip", tip, "--message", TITLE)
    refused = lem(capsys, world.checkout, "land", "merge", FEATURE, *owner)
    refusal = refused["refusal"]
    assert isinstance(refusal, dict)
    assert refusal["code"] == "pulls-into-feature", refused
    assert f"#{theirs.number} from docs/teammate ({theirs.url})" in refusal["why"]
    assert world.repo.head_of("main") == main
    assert world.forge.merge_calls[-1][0] != 3
