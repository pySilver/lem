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
import signal
import subprocess
import sys
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
from lem.kernel import files
from lem.ports.faults import Unanswered
from lem.ports.place import Place
from lem.records.landing.record import Landing
from lem.store import tasks
from unit.cli import parsing, reading, shapes

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from lem.ports.forge import Forge
    from lem.ports.forge_facts import MergeMethod, MergeText
    from lem.ports.git import Git
    from lem.records.landing.checks import Outcome
    from lem.records.record import Record
    from lem.store.tasks import Change

type Envelope = dict[str, Any]
TREE = shapes.tree()

SLUG = "readme-says-receive"
BRANCH = f"docs/{SLUG}"
SETTINGS = b"""[branch]
base = "main"
land = "agent"
history = "squash"

[checks]
commands = ["grep -q receive README.md", "test -f README.md"]
"""
CRITERIA = """## Acceptance criteria

Size: small, because it is one word of the README.

1. The README says receive, not recieve.
"""
NO_TEST = "   - no test: the change keeps behavior; the suite holds it\n"
# The review agent's record, in the form `prompts/review.md` gives it; its attempt and tip are
# the ones `lem land read` printed. Its defect outside the change is cheap: a line of the pull
# request, which `file` writes no item and no commit for (an item is
# `tests/journeys/landing/test_review.py`'s).
REVIEW = {
    "kind": "read",
    "ran": [{"name": "claude", "why": "one read of one word"}],
    "left_out": [],
    "answered": ["claude"],
    "silent": [],
    "must_fix": 0,
    "should": 0,
    "nit": 0,
    "outside": [
        {
            "where": "README.md",
            "title": "the README has no heading",
            "what": "README.md starts with a sentence",
            "bar": "cheap",
            "why": "a heading changes nothing a reader of one line needs",
        }
    ],
    "careful": False,
    "careful_why": "one word of the README reaches nothing that must never go wrong",
}
SUBJECT = "docs: the README says receive"
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
        """How many times each act of a port but a fetch was done."""
        return Counter(name for name in self.done if name in ACTS and name != "fetch")


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
    observed(monkeypatch, acts)
    monkeypatch.chdir(folder)
    return world


def observed(monkeypatch: pytest.MonkeyPatch, acts: Acts) -> None:
    """Count, and let a test cut after, the effects that are no act of a port: an artifact
    published, a record written (with what it newly holds), and one command of the checks."""
    publish, update, output_of = files.publish, tasks.update, checks_run.output_of

    def published(path: Path, body: bytes) -> str:
        made = publish(path, body)
        kind = "checks" if path.parent.name == "checks" else path.name.split("-")[0]
        acts.after(f"publish:{kind}")
        return made

    def written(state: Path, slug: str, change: Change, expect: int) -> Record:
        before = tasks.read(state, slug).landing
        after = update(state, slug, change, expect)
        for name in news(before, after.landing):
            acts.after(f"write:{name}")
        return after

    def ran(context: frame.Context, command: str) -> tuple[int, bytes]:
        made = output_of(context, command)
        acts.after("command")
        return made

    monkeypatch.setattr(files, "publish", published)
    monkeypatch.setattr(tasks, "update", written)
    monkeypatch.setattr(checks_run, "output_of", ran)


def news(before: Landing | None, after: Landing | None) -> list[str]:
    """What a write newly holds of the landing: the push, the intent, the merge, the end."""
    if after is None:
        return []
    was = before or Landing()
    found = [
        ("pushed", after.pushed and after.pushed != was.pushed),
        ("intent", after.intent and not was.intent),
        ("merged", after.merged and not was.merged),
        ("ended", after.phase == "ended" and was.phase != "ended"),
    ]
    return [name for name, new in found if new]


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


def due_read(capsys: pytest.CaptureFixture[str], world: World) -> Envelope:
    """What review is due; its attempt and tip go to the review's record."""
    envelope = lem(capsys, world.checkout, "land", "read", SLUG)
    world.told.update(tip=envelope["result"]["tip"])
    world.told.update(attempt=str(envelope["result"]["attempt"]))
    return envelope


def review(capsys: pytest.CaptureFixture[str], world: World) -> Envelope:
    """The review agent's record of its read, for the attempt and tip that are due."""
    said = {**REVIEW, "attempt": int(world.told["attempt"]), "tip": world.told["tip"]}
    record = world.written("review.json", said)
    return lem(capsys, world.checkout, "land", "read", SLUG, "--record", record)


def proposal(capsys: pytest.CaptureFixture[str], world: World) -> Envelope:
    """The pull request, with the agent's title and notes."""
    notes = world.written("notes.md", "none\n")
    title = ("--title", SUBJECT, "--notes", notes)
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
    ("read", due_read),
    ("read", review),
    ("file", command("land", "file", "SLUG")),
    ("propose", proposal),
    ("merge-review", brief),
    ("merge-review", reply),
    ("merge", command("land", "merge", "SLUG", "--by", "merger", "--message", SUBJECT)),
    ("merged", command("land", "merged", "SLUG")),
    ("clean", command("land", "clean", "SLUG")),
)
next_step = command("land", "next", "SLUG")


def due(capsys: pytest.CaptureFixture[str], world: World) -> str:
    """The step `lem land next` names."""
    return str(next_step(capsys, world)["result"]["step"])


def parses(envelope: Envelope) -> None:
    """The envelope's next command is a line the tree takes, its inputs as placeholders."""
    command = envelope.get("next", {}).get("command")
    if command is None:
        return
    line = reading.Line("next", 1, command, span=False)
    assert reading.verdict(line, TREE) == [], command
    assert parsing.clicks_word(line) is None, command


def after_kill(capsys: pytest.CaptureFixture[str], world: World, at: int) -> bool:
    """After a kill in the step at `at`: whether that step is due again; else the write it
    was killed after ended it, and the next one is due."""
    verb = JOURNEY[at][0]
    envelope = next_step(capsys, world)
    parses(envelope)
    found = envelope["result"]["step"]
    if found == verb:
        return True
    later = [name for name, _ in JOURNEY[at + 1 :] if name is not None and name != verb]
    assert found == (later[0] if later else "done"), (verb, found)
    return False


def journey(capsys: pytest.CaptureFixture[str], world: World) -> list[str]:
    """The whole journey: after a kill, the cut step is due again and its command runs again,
    or the write it was killed after ended it. Gives the steps that were cut."""
    cut: list[str] = []
    for at, (verb, step) in enumerate(JOURNEY):
        try:
            envelope = step(capsys, world)
        except Killed:
            capsys.readouterr()
            cut.append(verb or "task")
            if verb is not None and not after_kill(capsys, world, at):
                continue
            envelope = step(capsys, world)
        assert envelope["ok"] is True, envelope
        parses(envelope)
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
        parses(envelope)
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
    assert (
        "- `README.md`: the README has no heading; cheap: a heading changes nothing a "
        "reader of one line needs"
    ) in text


# Each act of the plain path, by its name and its count among the acts of that name; the second
# fetch is `lem land start`'s look at origin.
CUTS = (
    ("worktree_add", 1),
    ("publish:checks", 1),
    ("command", 1),
    ("publish:pr", 1),
    ("write:pushed", 1),
    ("publish:merge", 1),
    ("write:merged", 1),
    ("write:ended", 1),
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
    assert len(list((world.task_folder / "checks").iterdir())) == 2


def upto(capsys: pytest.CaptureFixture[str], world: World, stop: str) -> None:
    """Run the journey up to the first command of the step `stop`."""
    for verb, step in JOURNEY:
        if verb == stop:
            return
        envelope = step(capsys, world)
        assert envelope["ok"] is True, envelope


MERGE = command("land", "merge", "SLUG", "--by", "merger", "--message", SUBJECT)


def test_a_cut_after_the_intent_and_before_the_call_waits_for_the_owner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    world.acts.cut = ("write:intent", 1)
    with pytest.raises(Killed):
        MERGE(capsys, world)
    capsys.readouterr()
    assert world.record()["landing"]["intent"]["tip"] == world.told["tip"]
    envelope = next_step(capsys, world)
    parses(envelope)
    assert envelope["result"] == {
        "step": "merge",
        "why": "a merge call is on record: it is reconciled first",
        "by": "merger",
    }
    refused = MERGE(capsys, world)["refusal"]
    assert refused["code"] == "intent"
    assert world.forge.merge_calls == []
    assert world.record()["landing"]["intent"] is not None


def lost(monkeypatch: pytest.MonkeyPatch, world: World, *, reached: bool) -> None:
    """The forge's merge call loses its reply once: after the forge merged (an act done, so
    counted), or before the call reached it."""
    merge, lose = world.forge.merge, [True]

    def merged(number: int, head: str, method: MergeMethod, text: MergeText) -> object:
        if lose and not reached:
            lose.pop()
            raise Unanswered("gh", "error connecting to api.github.com")
        made = merge(number, head, method, text)
        if lose:
            lose.pop()
            world.acts.done.append("merge")
            raise Unanswered("gh", "read tcp: connection reset by peer")
        return made

    monkeypatch.setattr(world.forge, "merge", merged)


def test_a_lost_reply_after_the_merge_is_reconciled_and_lands_with_one_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    lost(monkeypatch, world, reached=True)
    faulted = MERGE(capsys, world)
    assert (faulted["code"], faulted["ok"]) == (3, False)
    assert world.record()["landing"]["intent"] is not None
    assert due(capsys, world) == "merge"
    assert MERGE(capsys, world)["ok"] is True
    for step in (command("land", "merged", "SLUG"), command("land", "clean", "SLUG")):
        assert step(capsys, world)["ok"] is True
    assert_landed(world)


def test_a_lost_reply_before_the_call_keeps_the_intent_and_calls_no_more(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    lost(monkeypatch, world, reached=False)
    assert MERGE(capsys, world)["code"] == 3
    assert MERGE(capsys, world)["refusal"]["code"] == "intent"
    assert world.forge.merge_calls == []
    assert world.forge.pulls[1].state == "open"


def test_githubs_refusal_is_kept_in_its_words_and_waits_for_the_owner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    world.forge.refuse = "Required status check is expected"
    refused = MERGE(capsys, world)["refusal"]
    assert refused["code"] == "github"
    landing = world.record()["landing"]
    assert landing["refused"]["line"] == "Required status check is expected"
    assert "intent" not in landing or landing["intent"] is None
    envelope = next_step(capsys, world)
    assert envelope["result"]["step"] == "wait"
    assert envelope["next"]["do"] == "wait"
    assert MERGE(capsys, world)["refusal"]["code"] == "not-due"
    assert len(world.forge.merge_calls) == 1


def test_the_squash_takes_the_reports_subject_and_names_the_task(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    bare = command("land", "merge", "SLUG", "--by", "merger")(capsys, world)
    assert bare["refusal"]["code"] == "message"
    assert world.forge.merge_calls == []
    assert MERGE(capsys, world)["ok"] is True
    said = run_git(world.repo.origin, "log", "-1", "--format=%B", "main")
    assert said.startswith(f"{SUBJECT}\n")
    assert said.rstrip().endswith(f"Lem task: {SLUG}")


def test_a_cut_after_the_pull_requests_edit_adopts_it_and_edits_it_no_more(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "propose")
    world.acts.cut = ("open_pull", 1)
    with pytest.raises(Killed):
        proposal(capsys, world)
    capsys.readouterr()
    world.acts.cut = ("update_pull", 1)
    notes = world.written(
        "notes.md",
        "- `README.md`: written again after the stop; under: one line says it\n",
    )
    words = ("--title", SUBJECT, "--notes", notes)
    with pytest.raises(Killed):
        command("land", "propose", "SLUG", *words)(capsys, world)
    capsys.readouterr()
    assert command("land", "propose", "SLUG", *words)(capsys, world)["ok"] is True
    assert world.acts.counted()["update_pull"] == 1
    assert world.acts.counted()["open_pull"] == 1
    assert "written again after the stop" in world.forge.bodies[1]


def test_a_step_lock_of_a_process_that_died_is_free_and_of_one_alive_is_held(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "checks")
    state = world.checkout / ".lem" / "state"
    holder = subprocess.Popen(
        [sys.executable, "-I", "-B", "-c", HOLDER, str(state), SLUG],
        stdout=subprocess.PIPE,
        text=True,
    )
    assert holder.stdout is not None
    assert holder.stdout.readline().strip() == "held"
    held = command("land", "checks", "SLUG")(capsys, world)["refusal"]
    assert held["code"] == "step-held"
    holder.send_signal(signal.SIGKILL)
    holder.wait(timeout=30)
    assert command("land", "checks", "SLUG")(capsys, world)["ok"] is True


# A process that holds a task's step lock until it is killed.
HOLDER = """
import sys, time
from datetime import UTC, datetime
from pathlib import Path
from lem.store import steps
with steps.step(Path(sys.argv[1]), sys.argv[2], "checks", datetime.now(UTC).replace(microsecond=0)):
    print("held", flush=True)
    time.sleep(120)
"""


def test_a_protected_base_takes_no_merge_and_the_forge_gets_no_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    settings = world.checkout / ".lem" / "settings.toml"
    guarded = settings.read_text().replace(
        'history = "squash"', 'history = "squash"\nprotected = ["main"]'
    )
    settings.write_text(guarded)
    refused = MERGE(capsys, world)["refusal"]
    assert refused["code"] == "protected"
    assert world.forge.merge_calls == []


def test_a_careful_small_task_is_not_green_and_the_merge_agent_does_not_merge_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    careful = command(
        "task",
        "read",
        "SLUG",
        "--type",
        "docs",
        "--why",
        "a word",
        "--track",
        "small",
        "--then",
        "fast",
        "--careful",
        "a customer is charged",
    )
    full = {**REVIEW, "kind": "full", "left_out": []}
    for verb, step in JOURNEY:
        if verb == "merge":
            break
        run = careful if step is JOURNEY[1][1] else step
        if step is review:
            said = {
                **full,
                "attempt": int(world.told["attempt"]),
                "tip": world.told["tip"],
            }
            record = world.written("review.json", said)
            run = command("land", "read", "SLUG", "--record", record)
        if step is proposal:
            # a careful request's notes say whether it holds a migration
            notes = world.written("notes.md", "none\n\n## Migration\n\nnone\n")
            run = command(
                "land", "propose", "SLUG", "--title", SUBJECT, "--notes", notes
            )
        envelope = run(capsys, world)
        assert envelope["ok"] is True, envelope
    proposed = world.record()["landing"]["proposed"]
    assert proposed["green"] is False
    assert proposed["reasons"][0].startswith(
        "careful on the fast track (a customer is charged): it took the fast track"
    )
    assert next_step(capsys, world)["next"]["do"] == "wait"
    assert MERGE(capsys, world)["refusal"]["code"] == "merger-rule"
    assert world.forge.merge_calls == []


def snapshot(folder: Path) -> dict[str, tuple[bytes, int]]:
    """Every file under `folder`, with its bytes and its time of change."""
    return {
        str(path): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in sorted(folder.rglob("*"))
        if path.is_file()
    }


# Each command an agent runs on a task of the fast track, the landing's steps among them.
EVERY = (
    ("task", "open", "SLUG", "--ask", "the README says recieve"),
    ("task", "worktree", "SLUG"),
    ("land", "next", "SLUG"),
    ("land", "start", "SLUG"),
    ("land", "base", "SLUG"),
    ("land", "checks", "SLUG"),
    ("land", "read", "SLUG"),
    ("land", "file", "SLUG"),
    ("land", "propose", "SLUG", "--title", "docs: receive", "--notes", "notes.md"),
    ("land", "merge-review", "SLUG"),
    ("land", "merge", "SLUG", "--by", "merger"),
    ("land", "merged", "SLUG"),
    ("land", "clean", "SLUG"),
)


@pytest.mark.parametrize("argv", EVERY, ids=[" ".join(argv[:2]) for argv in EVERY])
def test_a_workspace_with_the_state_of_lem_0_3_is_refused_before_any_act(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    argv: tuple[str, ...],
) -> None:
    world = made(tmp_path, monkeypatch)
    state = world.checkout / ".lem" / "state"
    state.mkdir(parents=True)
    (state / ".gitignore").write_text("*\n")
    (state / "events.jsonl").write_text(
        '{"event": "task.open", "task": "an-old-task"}\n'
    )
    before = snapshot(world.repo.origin.parent)
    refused = command(*argv)(capsys, world)
    assert (refused["code"], refused["refusal"]["code"]) == (1, "old-state")
    assert world.acts.done == []
    assert world.forge.pulls == {}
    assert snapshot(world.repo.origin.parent) == before
