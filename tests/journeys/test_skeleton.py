"""The walking skeleton of the landing: one fast-track task from `lem task open` to `landed`,
on a real repository and `LocalForge`, with the commands an agent runs, each through the tree in
this process (`lem.cli.lazy.main`) with `--repo` to the test's own repository.

Then the same journey cut off after each effect, before its record (`Killed`, as a process
killed there), and run on: `lem land next` names the cut step again from what git and the forge
show, the cut command runs again, and no effect is done twice (the forge's merge calls are
counted, as trial R5 does).

The ports are bound by the test (`wiring.bound` replaced): real git through `lem.adapters.
git_cli`, and `LocalForge` over the repository's origin. The working directory is a temporary
folder in no repository, so a call that forgot `--repo` touches nothing.
"""

import json
from collections import Counter
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, cast

import pytest

from fakes.forge import LocalForge
from fakes.harness import FakeHarness
from fakes.outside import FakeJudge, FakeTracker, RecordingNotifier
from fakes.repo import RealRepo, git_env, run_git
from fakes.terminal import FakeTerminal
from lem.adapters import git_cli
from lem.app import wiring
from lem.app.landing import checks_run, frame
from lem.cli import lazy
from lem.ports.place import Place

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from lem.ports.forge import Forge
    from lem.ports.git import Git
    from lem.records.landing.checks import Outcome

type Envelope = dict[str, Any]

SLUG = "readme-says-receive"
BRANCH = f"docs/{SLUG}"
SETTINGS = b"""[branch]
base = "main"
land = "agent"
history = "squash"

[checks]
commands = ["grep -q receive README.md"]
"""
CRITERIA = """## Acceptance criteria

Size: small, because it is one word of the README.

1. The README says receive, not recieve.
"""
NO_TEST = "   - no test: the change keeps behavior; the suite holds it\n"
REVIEW = {
    "kind": "read",
    "answered": ["claude"],
    "careful": False,
    "careful_why": "one word of the README reaches nothing that must never go wrong",
    "findings": [
        {
            "id": "r1.1",
            "level": "nit",
            "where": "README.md",
            "title": "the README has no heading",
            "what": "README.md starts with a sentence",
            "against": "under",
            "why": "a heading changes nothing a reader of one line needs",
        }
    ],
}
# The acts of the ports, after each of which a process may be killed before its record.
ACTS = frozenset(
    (
        "fetch",
        "rebase",
        "abort",
        "commit",
        "push",
        "worktree_add",
        "worktree_remove",
        "branch_delete",
        "fast_forward",
        "open_pull",
        "update_pull",
        "merge",
        "delete_ref",
    )
)
# The acts of the journey with no cut, but its fetches: each once.
ONCE = Counter(
    (
        "worktree_add",
        "rebase",
        "push",
        "open_pull",
        "merge",
        "fast_forward",
        "worktree_remove",
        "branch_delete",
        "delete_ref",
    )
)


class Killed(BaseException):
    """The process ended between an effect and its record."""


@dataclass
class Acts:
    """Every act of the ports in order, and the act (its name and how many of that name came
    before it, counting from 1) after which the process is killed once."""

    done: list[str] = field(default_factory=list)
    cut: tuple[str, int] | None = None

    def after(self, name: str) -> None:
        """Count the act `name`; kill the process when it is the cut one."""
        self.done.append(name)
        if self.cut == (name, self.done.count(name)):
            self.cut = None
            raise Killed(name)

    def counted(self) -> Counter[str]:
        """How many times each act but a fetch was done."""
        return Counter(name for name in self.done if name != "fetch")


@dataclass
class Counted:
    """A port whose acts `Acts` counts and may cut after; its facts pass through."""

    inner: object
    acts: Acts

    def __getattr__(self, name: str) -> object:
        found = getattr(self.inner, name)
        if name not in ACTS:
            return found

        def acted(*args: object, **kwargs: object) -> object:
            outcome = found(*args, **kwargs)
            self.acts.after(name)
            return outcome

        return acted


@dataclass
class World:
    """The test's repository, its forge, the acts, its folder, and what one step tells the
    next (the brief's tip and base)."""

    repo: RealRepo
    forge: LocalForge
    acts: Acts
    folder: Path
    told: dict[str, str] = field(default_factory=dict)

    @property
    def checkout(self) -> Path:
        return self.repo.checkout

    @property
    def worktree(self) -> Path:
        return self.checkout / ".lem" / "worktrees" / SLUG

    @property
    def task_folder(self) -> Path:
        return self.checkout / ".lem" / "state" / "tasks" / SLUG

    def record(self) -> Envelope:
        return json.loads((self.task_folder / "task.json").read_text())

    def written(self, name: str, body: object) -> str:
        """A file the agent writes for a command, outside the repository."""
        path = self.folder / name
        path.write_text(body if isinstance(body, str) else json.dumps(body))
        return str(path)


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
    monkeypatch.chdir(folder)
    return world


def lem(capsys: pytest.CaptureFixture[str], where: Path, *argv: str) -> Envelope:
    """`lem --repo WHERE ARGV` in this process: its envelope, with its exit code."""
    code = lazy.main(["--repo", str(where), *argv])
    out = capsys.readouterr().out
    return {**json.loads(out), "code": code}


type Step = Callable[[pytest.CaptureFixture[str], World], Envelope]


def command(*argv: str, inside: bool = False) -> Step:
    """`lem ARGV` with the task's slug for SLUG, run in the main checkout or, `inside`, in
    the task's worktree."""
    words = [SLUG if word == "SLUG" else word for word in argv]

    def run(capsys: pytest.CaptureFixture[str], world: World) -> Envelope:
        return lem(capsys, world.worktree if inside else world.checkout, *words)

    return run


def criteria(capsys: pytest.CaptureFixture[str], world: World) -> Envelope:
    """The task's session writes the criterion into the task's folder."""
    (world.task_folder / "criteria.md").write_text(CRITERIA)
    return {"ok": True}


def built(capsys: pytest.CaptureFixture[str], world: World) -> Envelope:
    """The builder's change, committed on the task's branch, and its criterion's line."""
    (world.worktree / "README.md").write_text("The README says receive.\n")
    run_git(world.worktree, "commit", "--quiet", "--all", "--message", "docs: receive")
    with (world.task_folder / "criteria.md").open("a") as found:
        found.write(NO_TEST)
    return {"ok": True}


def teammate(capsys: pytest.CaptureFixture[str], world: World) -> Envelope:
    """A teammate's commit on the base, so that the landing rebases."""
    world.repo.outside_commit("main", {"NOTES.md": b"a teammate's note\n"})
    return {"ok": True}


def review(capsys: pytest.CaptureFixture[str], world: World) -> Envelope:
    """The review agent's record of its read."""
    record = world.written("review.json", REVIEW)
    return lem(capsys, world.checkout, "land", "read", SLUG, "--record", record)


def proposal(capsys: pytest.CaptureFixture[str], world: World) -> Envelope:
    """The pull request, with the agent's title and notes."""
    notes = world.written("notes.md", "No decision was taken; nothing is left open.\n")
    title = ("--title", "docs: the README says receive", "--notes", notes)
    return lem(capsys, world.checkout, "land", "propose", SLUG, *title)


def brief(capsys: pytest.CaptureFixture[str], world: World) -> Envelope:
    """The merge agent's brief; its tip and base go to the reply."""
    envelope = lem(capsys, world.checkout, "land", "merge-review", SLUG)
    world.told.update(tip=envelope["result"]["tip"], base=envelope["result"]["base"])
    return envelope


def reply(capsys: pytest.CaptureFixture[str], world: World) -> Envelope:
    """The merge agent's reply to the brief, with its tip and base."""
    said = world.written(
        "reply.md", "merge\n\nOne word; the checks and the read hold.\n"
    )
    words = ("--file", said, "--tip", world.told["tip"], "--base", world.told["base"])
    return lem(capsys, world.checkout, "land", "merge-review", SLUG, *words)


# The journey, one command or one act of an agent at a time, each with the step `lem land
# next` names before it (None before the landing).
JOURNEY: tuple[tuple[str | None, Step], ...] = (
    (None, command("task", "open", "SLUG", "--ask", "the README says recieve; fix it")),
    (
        None,
        command(
            "task",
            "read",
            "SLUG",
            "--type",
            "docs",
            "--why",
            "a word of the README",
            "--track",
            "small",
            "--then",
            "fast",
        ),
    ),
    (None, criteria),
    (None, command("criteria", "approve", "SLUG", "--small")),
    (None, command("task", "worktree", "SLUG")),
    (None, command("task", "move", "SLUG", "building", "--line", "one builder")),
    (None, built),
    (None, command("criteria", "record", "SLUG", inside=True)),
    (None, teammate),
    (None, command("task", "move", "SLUG", "ready", "--line", "built", inside=True)),
    ("start", command("land", "start", "SLUG")),
    ("base", command("land", "base", "SLUG")),
    ("checks", command("land", "checks", "SLUG")),
    ("read", command("land", "read", "SLUG")),
    ("read", review),
    ("file", command("land", "file", "SLUG")),
    ("propose", proposal),
    ("merge-review", brief),
    ("merge-review", reply),
    ("merge", command("land", "merge", "SLUG", "--by", "merger")),
    ("merged", command("land", "merged", "SLUG")),
    ("clean", command("land", "clean", "SLUG")),
)
next_step = command("land", "next", "SLUG")


def due(capsys: pytest.CaptureFixture[str], world: World) -> str:
    """The step `lem land next` names."""
    return str(next_step(capsys, world)["result"]["step"])


def journey(capsys: pytest.CaptureFixture[str], world: World) -> list[str]:
    """The whole journey: after a kill, the cut step is due again and its command runs again.
    Gives the steps that were cut."""
    cut: list[str] = []
    for verb, step in JOURNEY:
        try:
            envelope = step(capsys, world)
        except Killed:
            capsys.readouterr()
            cut.append(verb or "task")
            if verb is not None:
                assert due(capsys, world) == verb
            envelope = step(capsys, world)
        assert envelope["ok"] is True, envelope
    return cut


def assert_landed(world: World) -> None:
    """The task landed, its landing ended, and nothing of it is left but the base's commit."""
    found = world.record()
    assert found["task"]["status"] == "landed"
    assert found["landing"]["phase"] == "ended"
    assert not world.worktree.exists()
    assert run_git(world.checkout, "branch", "--list", BRANCH) == ""
    assert world.repo.head_of(BRANCH) is None
    assert (
        run_git(world.repo.origin, "show", "main:README.md")
        == "The README says receive."
    )
    assert (world.checkout / "README.md").read_text() == "The README says receive.\n"
    assert (world.checkout / "NOTES.md").is_file()
    assert [number for number, _ in world.forge.merge_calls] == [1]
    assert len(world.forge.pulls) == 1
    assert run_git(world.checkout, "status", "--porcelain") == ""
    assert world.acts.counted() == ONCE


def test_a_fast_track_task_lands_and_each_step_is_the_due_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    for verb, step in JOURNEY:
        if verb is not None or world.task_folder.is_dir():
            assert due(capsys, world) == (verb or "none")
        envelope = step(capsys, world)
        assert envelope["ok"] is True, envelope
        if verb == "start":
            early = command("land", "checks", "SLUG")(capsys, world)["refusal"]
            assert early["code"] == "not-due"
            assert early["fix"] == f"lem land base {SLUG} is the step that is due"
        if verb == "propose":
            assert envelope["result"]["green"] is True
            assert proposal(capsys, world)["refusal"]["code"] == "not-due"
    assert due(capsys, world) == "done"
    after = command("land", "clean", "SLUG")(capsys, world)["refusal"]
    assert (after["code"], after["fix"]) == (
        "not-due",
        "no step is due: the landing ended",
    )
    assert_landed(world)
    named = world.record()["landing"]["proposed"]["text"]
    text = (world.task_folder / named).read_text()
    assert text.startswith("**Green.**")
    assert "   - no test: the change keeps behavior; the suite holds it" in text
    assert "- r1.1: under: a heading changes nothing a reader of one line needs" in text


# Each act of the plain path, by its name and its count among the acts of that name; the second
# fetch is `lem land start`'s look at origin.
CUTS = (
    ("worktree_add", 1),
    ("fetch", 2),
    ("rebase", 1),
    ("push", 1),
    ("open_pull", 1),
    ("merge", 1),
    ("fast_forward", 1),
    ("worktree_remove", 1),
    ("branch_delete", 1),
    ("delete_ref", 1),
)


@pytest.mark.parametrize("cut", CUTS, ids=[f"{name}-{count}" for name, count in CUTS])
def test_a_cut_after_an_effect_is_due_again_and_does_nothing_twice(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    cut: tuple[str, int],
) -> None:
    world = made(tmp_path, monkeypatch)
    world.acts.cut = cut
    assert len(journey(capsys, world)) == 1
    assert world.acts.cut is None
    assert_landed(world)


def test_a_cut_after_the_checks_ran_runs_them_again_and_lands(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    ran = checks_run.every
    kills = [True]

    def every(context: frame.Context) -> tuple[Outcome, ...]:
        outcomes = ran(context)
        if kills:
            kills.pop()
            raise Killed("checks")
        return outcomes

    monkeypatch.setattr(checks_run, "every", every)
    assert journey(capsys, world) == ["checks"]
    assert_landed(world)
    assert len(list((world.task_folder / "checks").iterdir())) == 1
