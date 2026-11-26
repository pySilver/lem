"""The standard track end to end, through the commands a task's session, its lead, its builders,
the review, the merge agent and the board's server run: the request's read, the interview's
criteria and the owner's yes, the plan in the task's worktree, the plan's count, his build, the
build, the landing with its polish pass, a round of review, the pull request, the merge read, the
merge, its bookkeeping and the cleanup, on a real repository and `LocalForge`.

Each command runs through the tree in this process, as `tests/journeys/test_skeleton.py` runs
the fast track, whose world this module takes; `lem land next` names each landing step before
it runs.
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from fakes.repo import run_git
from fakes.terminal import FakeTerminal
from journeys.agent import ok
from journeys.test_skeleton import REVIEW, SLUG, lem, made, parses
from lem.app import wiring
from lem.ports.place import Place
from lem.ports.terminal import Pane

if TYPE_CHECKING:
    from pathlib import Path

    from journeys.test_skeleton import Envelope, World

type Capsys = pytest.CaptureFixture[str]

TITLE = "docs: the README says receive"
CRITERIA = """## Acceptance criteria

Size: full, because the README and its check change together.

1. The README says receive, not recieve: `grep receive README.md` finds the line.
"""
TESTS = "   - test: `sh tests/receive.sh` in `tests/receive.sh`\n"
TASKS = "\n## Tasks\n\n1. Say receive in the README, with its test.\n"
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


def due(capsys: Capsys, world: World) -> str:
    """The landing step `lem land next` names."""
    return str(ok(capsys, world, "land", "next", SLUG)["result"]["step"])


def step(
    capsys: Capsys, world: World, verb: str, *words: str, ok: bool = True
) -> Envelope:
    """`lem land VERB SLUG WORDS`, which `lem land next` names first; it succeeds, unless
    `ok` is false. `propose` takes the lead's title and the notes' five headings."""
    assert due(capsys, world) == verb
    if verb == "propose":
        words = ("--title", TITLE, "--notes", world.written("notes.md", NOTES))
    envelope = lem(capsys, world.checkout, "land", verb, SLUG, *words)
    assert envelope["ok"] is ok, envelope
    parses(envelope)
    return envelope


def commit(world: World, files: dict[str, str], subject: str) -> str:
    """A commit of `files` on the task's branch, in its worktree; its sha."""
    for name, body in files.items():
        path = world.worktree / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)
    run_git(world.worktree, "add", "--all")
    run_git(world.worktree, "commit", "--quiet", "--message", subject)
    return run_git(world.worktree, "rev-parse", "HEAD")


def shaped(capsys: Capsys, world: World) -> None:
    """The request's read and the interview: his criteria, approved by his yes."""
    ok(capsys, world, "task", "open", SLUG, "--ask", "the README says recieve; fix it")
    interviewed(capsys, world)


def interviewed(capsys: Capsys, world: World) -> None:
    """The read of the open request and its interview: his criteria, approved by his yes."""
    ok(
        capsys,
        world,
        "task",
        "read",
        SLUG,
        "--type",
        "docs",
        "--why",
        "a word of the README and its check",
        "--track",
        "full",
        "--then",
        "interview",
    )
    ok(capsys, world, "task", "span", SLUG, "interview", "start")
    answered = world.written("criteria.md", CRITERIA)
    ok(capsys, world, "criteria", "skip", SLUG, "asked")
    ok(capsys, world, "criteria", "skip", SLUG, "yes")
    ok(capsys, world, "criteria", "approve", SLUG, "--file", answered)
    ok(capsys, world, "task", "span", SLUG, "interview", "end")


def started(capsys: Capsys, world: World) -> None:
    """The build's start: the task's worktree, and the task `building`."""
    ok(capsys, world, "task", "worktree", SLUG)
    ok(capsys, world, "task", "move", SLUG, "building", "--line", "the lead plans")


def planned(
    capsys: Capsys, world: World, tasks: str = TASKS, *, start: bool = True
) -> str:
    """The lead's plan, in the task's worktree, and its count: the task is `planned`; the
    build starts first unless `start` is false."""
    if start:
        started(capsys, world)
    ok(capsys, world, "task", "span", SLUG, "lead", "start", "--by", "session")
    name = ok(capsys, world, "task", "plan-file", SLUG)["result"]["path"]
    commit(world, {name: CRITERIA + TESTS + tasks}, "docs: the plan")
    ok(capsys, world, "criteria", "record", SLUG, inside=True)
    count = str(sum(line[:1].isdigit() for line in tasks.splitlines()))
    written = ok(capsys, world, "task", "planned", SLUG, "--tasks", count)["result"]
    assert ok(capsys, world, "task", "show", SLUG)["result"]["plan"] == written
    return name


def built(capsys: Capsys, world: World, plan: str) -> None:
    """His build of the plan, by its file, and the builder's commit: the task is `ready`."""
    ok(capsys, world, "task", "build", plan)
    commit(
        world,
        {
            "README.md": "The README says receive.\n",
            "tests/receive.sh": "grep -q receive README.md\n",
        },
        "docs: the README says receive",
    )
    ok(capsys, world, "task", "move", SLUG, "ready", "--line", "built", inside=True)


def prepared(capsys: Capsys, world: World) -> None:
    """The landing of the standard track up to its proposal, each step the one `lem land next`
    names: the polish pass commits a note, and one round of review finds nothing."""
    step(capsys, world, "start")
    step(capsys, world, "base")
    brief = step(capsys, world, "polish")["result"]
    assert brief["done"] is False
    commit(world, {"NOTES.md": "a note the polish pass wrote\n"}, "docs: a note")
    ok(capsys, world, "land", "polish", SLUG, "--done")
    step(capsys, world, "checks")
    told = step(capsys, world, "read")["result"]
    said = {**ROUND, "attempt": told["attempt"], "tip": told["tip"]}
    ok(capsys, world, "land", "read", SLUG, "--record", world.written("r.json", said))


def onward(capsys: Capsys, world: World) -> list[str]:
    """The landing steps `lem land next` names, run until `propose` is due: the steps that
    ran. Nothing in this module asks a second polish pass or a second read."""
    ran: list[str] = []
    while (verb := due(capsys, world)) != "propose":
        assert verb in {"start", "base", "checks", "file"}, (verb, ran)
        ok(capsys, world, "land", verb, SLUG)
        ran.append(verb)
    return ran


def merged(capsys: Capsys, world: World) -> None:
    """The merge agent's read and the merge, its bookkeeping and the cleanup."""
    read = step(capsys, world, "merge-review")["result"]
    reply = world.written("reply.md", "Verdict: merge\n\nThe word and its test.\n")
    pinned = (
        "--tip",
        read["tip"],
        "--base",
        read["base"],
        "--dispatch",
        str(read["dispatch"]),
    )
    ok(capsys, world, "land", "merge-review", SLUG, "--file", reply, *pinned)
    step(capsys, world, "merge", "--by", "merger", "--message", TITLE)
    step(capsys, world, "merged")
    step(capsys, world, "clean")


def test_a_standard_task_goes_from_its_request_to_a_cleaned_merge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    shaped(capsys, world)
    record = world.record()["task"]
    assert record["status"] == "shaping"
    assert [one["by"] for one in record["criteria"]["approvals"]] == ["owner"]
    plan = planned(capsys, world)
    record = world.record()["task"]
    assert (record["status"], record["plan"]) == ("planned", {"path": plan, "tasks": 1})
    waiting = ok(capsys, world, "task", "build")["result"]["waiting"]
    assert [(one["slug"], one["plan"]) for one in waiting] == [(SLUG, plan)]
    built(capsys, world, plan)
    assert world.record()["task"]["status"] == "ready"
    prepared(capsys, world)
    proposed = step(capsys, world, "propose")
    assert proposed["result"]["green"] is True, proposed
    assert world.record()["task"]["status"] == "open"
    merged(capsys, world)
    record = world.record()
    assert (record["task"]["status"], record["landing"]["phase"]) == ("landed", "ended")
    assert [span["name"] for span in record["task"]["spans"]] == [
        "interview",
        "lead",
        "polish",
        "checks",
        "review",
    ]
    assert not world.worktree.exists()
    assert run_git(world.checkout, "branch", "--list", "docs/*") == ""
    assert (
        run_git(world.repo.origin, "show", "main:README.md")
        == "The README says receive."
    )
    assert (
        run_git(world.repo.origin, "show", "main:NOTES.md")
        == "a note the polish pass wrote"
    )
    assert [number for number, _ in world.forge.merge_calls] == [1]
    body = world.forge.bodies[1]
    assert body.startswith("**Green.**")
    assert (
        "   - `sh tests/receive.sh`: passes on the branch, fails on the base commit"
        in body
    )
    assert "- the polish pass: 1 commit, 0 items filed in the backlog" in body
    assert "- the plan talk" not in body


TALK = (
    "--reviewer",
    "codex",
    "--turns",
    "23",
    "--questions",
    "5",
    "--settled",
    "4",
    "--open",
    "1",
    "--repaired",
    "1",
    "--design",
    "0",
    "--unargued",
    "0",
    "--root",
    "0",
    "--layer",
    "0",
    "--shared",
    "0",
)
FOUR = "\n## Tasks\n\n1. The word.\n2. Its test.\n3. A note.\n4. The check.\n"


def test_a_plan_of_four_tasks_is_proposed_only_after_its_plan_talk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    shaped(capsys, world)
    built(capsys, world, planned(capsys, world, tasks=FOUR))
    prepared(capsys, world)
    other = "notes-say-receive"
    ok(capsys, world, "task", "open", other, "--ask", "fix the notes")
    ok(capsys, world, "task", "span", other, "plan-talk", "start", "--by", "codex")
    assert ok(capsys, world, "task", "talked", other, *TALK)["result"]["slug"] == other
    refused = step(capsys, world, "propose", ok=False)["refusal"]
    assert refused["code"] == "plan-talk"
    assert "the plan has 4 tasks, more than three" in refused["why"]
    assert world.forge.pulls == {}
    line = "needs a session: the plan has 4 tasks, more than three"
    ok(capsys, world, "task", "move", SLUG, "planned", "--line", line)
    ok(capsys, world, "task", "span", SLUG, "plan-talk", "start", "--by", "codex")
    written = ok(capsys, world, "task", "talked", SLUG, *TALK)["result"]["talk"]
    assert ok(capsys, world, "task", "show", SLUG)["result"]["talk"] == written
    ok(capsys, world, "task", "build", SLUG)
    ok(capsys, world, "task", "move", SLUG, "ready", "--line", "talked", inside=True)
    assert onward(capsys, world) == ["start"]
    proposed = step(capsys, world, "propose")
    assert proposed["result"]["green"] is True, proposed
    body = world.forge.bodies[proposed["result"]["pull"]["number"]]
    talks = [line for line in body.splitlines() if line.startswith("- the plan talk")]
    talk = (
        "- the plan talk: codex argued the plan with its defender, 23 turns, over the bound "
        "of 22 for its 5 questions; 4 positions settled by the two, 1 left open; "
        "5 questions in the reviewer's first list, 1 "
        "repaired by the defender, 0 of the open ones a design choice, 0 raised after the "
        "list and not argued, 0 repaired at the cause, 0 layers over a cited decision, 0 "
        "decisions two questions named"
    )
    assert talks == [talk]
    merged(capsys, world)
    assert world.record()["task"]["status"] == "landed"


HANDOFF = """task: {slug} · from {phase} · written: {written}

## Settled

- {settled}

## Open

- none

## Next step

{next}

## Failed

- none

## Changed files

- none
"""


def handed(
    capsys: Capsys,
    world: World,
    terminal: FakeTerminal,
    leaving: tuple[str, str],
    settled: str,
) -> Envelope:
    """The handoff of the session that leaves, `leaving` (its id and its phase), and the
    session of the next phase, which that session opens."""
    session, phase = leaving
    terminal.caller = session
    then = "the next phase's first step"
    written = datetime.now(UTC).strftime("%Y-%m-%dT%H:%MZ")
    text = HANDOFF.format(
        slug=SLUG, phase=phase, written=written, settled=settled, next=then
    )
    (world.task_folder / "handoff.md").write_text(text)
    return ok(capsys, world, "session", "next", SLUG)


def test_each_phase_of_a_standard_task_has_a_session_of_its_own(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    terminal = wiring.bound(
        Place(checkout=world.checkout, home=tmp_path, environ={})
    ).terminal
    assert isinstance(terminal, FakeTerminal)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "claude"))
    terminal.caller = "S-MINE"
    terminal.panes["S-MINE"] = Pane(id="S-MINE", name="main", workspace="W-1")
    ok(capsys, world, "task", "open", SLUG, "--ask", "the README says recieve; fix it")
    opened = ok(capsys, world, "session", "open", SLUG, "--why", "new")
    assert (opened["result"]["phase"], opened["result"]["workspace"]) == (
        "shape",
        "W-1",
    )
    assert opened["next"]["command"] == f"lem session wait {SLUG} --first-line"
    interviewed(capsys, world)
    first = ok(capsys, world, "session", "wait", SLUG, "--first-line")["result"]
    assert first["gone"] is False
    started(capsys, world)
    shape = (opened["result"]["session"], "shape")
    build = handed(capsys, world, terminal, shape, "the criteria, approved")
    assert build["result"]["phase"] == "build"
    plan = planned(capsys, world, start=False)
    built(capsys, world, plan)
    leaving = (build["result"]["session"], "build")
    land = handed(capsys, world, terminal, leaving, f"the plan {plan}, built")
    assert land["result"]["phase"] == "land"
    prepared(capsys, world)
    step(capsys, world, "propose")
    merged(capsys, world)
    closed = ok(capsys, world, "session", "close", SLUG, "--why", "ended")["result"]
    assert closed["closed"] is True
    assert [one.name for one in terminal.openings] == [SLUG, SLUG, SLUG]
    assert terminal.closed == [land["result"]["session"]]
    listed = ok(capsys, world, "session", "list")["result"]
    assert [(one["task"], one["opened_in"]) for one in listed] == [(SLUG, "land")]
