"""The hard paths of the landing's start and base (`landing.md` E, proof owner `land-base`), each
a journey on a real repository and `LocalForge`, through the tree in this process with `--repo`
to the test's own repository, as `tests/journeys/test_skeleton.py` runs the plain path.

Recovery, no checks, a teammate's commit, a conflict with the base, a rebase git refuses, a
merge-only change, a conflicting pull request on the forge and the count of relands; and a cut
after each new effect of `start` and `base`, after which the step is due again and does nothing
twice.
"""

import shlex
import stat
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from fakes.repo import run_git
from journeys.agent import small_built, small_landed
from journeys.landing.test_merge import owner
from journeys.landing.test_propose import propose_with
from journeys.landing.test_review import UNDER, file_step, recorded, reviewed
from journeys.landing.test_review import brief as review_brief
from journeys.test_duties import served, ticked
from journeys.test_skeleton import (
    BRANCH,
    JOURNEY,
    SETTINGS,
    SLUG,
    Envelope,
    Killed,
    World,
    assert_landed,
    brief,
    command,
    lem,
    made,
    next_step,
    parses,
    proposal,
    reply,
    upto,
)
from lem.adapters import git_cli
from lem.kernel import clock
from lem.ports.faults import Unanswered
from lem.records.landing.start import Polished
from lem.store import tasks

if TYPE_CHECKING:
    from lem.records.record import Record

START = command("land", "start", "SLUG")
BASE = command("land", "base", "SLUG")
CHECKS = command("land", "checks", "SLUG")
CONFLICTING = command("land", "start", "SLUG", "--conflicting")
README = "The README says receive.\n"


def due(capsys: pytest.CaptureFixture[str], world: World) -> str:
    """The step `lem land next` names, its next line one the tree takes."""
    envelope = next_step(capsys, world)
    parses(envelope)
    return str(envelope["result"]["step"])


def refused(envelope: Envelope, code: str) -> dict[str, str]:
    """The refusal of a command, with its code and exit 1."""
    assert envelope["ok"] is False, envelope
    assert envelope["code"] == 1, envelope
    assert envelope["refusal"]["code"] == code, envelope
    return envelope["refusal"]


def ok(envelope: Envelope) -> Envelope:
    """A command that succeeded, its next line one the tree takes."""
    assert envelope["ok"] is True, envelope
    parses(envelope)
    return envelope


def landing(world: World) -> Envelope:
    """The landing as the record holds it."""
    return world.record()["landing"]


def head(world: World) -> str:
    """The commit the task's worktree is at."""
    return run_git(world.worktree, "rev-parse", "HEAD")


def test_a_second_landing_starts_in_the_same_workspace_while_the_first_is_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "start")
    ok(START(capsys, world))
    first = world.record()

    slug = "review-export"
    for args in (
        ("task", "open", slug, "--ask", "Review the export"),
        (
            "task",
            "read",
            slug,
            "--type",
            "docs",
            "--why",
            "a word of the export",
            "--track",
            "small",
            "--then",
            "fast",
        ),
        ("task", "worktree", slug),
        ("task", "move", slug, "building", "--line", "one builder"),
        ("task", "move", slug, "ready", "--line", "built"),
        ("land", "start", slug),
    ):
        ok(lem(capsys, world.checkout, *args))

    later = tasks.read(world.checkout / ".lem" / "state", slug)
    assert first["task"]["status"] == later.task.status == "landing"
    assert later.landing and later.landing.started
    assert world.record() == first
    assert later.task.branch != first["task"]["branch"]


@pytest.mark.parametrize("same_file", (False, True), ids=("other-file", "same-file"))
def test_a_careful_review_carries_over_a_clean_rebase(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    *,
    same_file: bool,
) -> None:
    world = made(tmp_path, monkeypatch)
    lines = [f"line {n}\n" for n in range(20)]
    numbered = world.checkout / "lines.txt"
    numbered.write_text("".join(lines))
    run_git(world.checkout, "add", numbered.name)
    run_git(world.checkout, "commit", "-m", "Add the numbered lines")
    run_git(world.checkout, "push", "origin", "main")
    upto(capsys, world, "start")
    tip = commit_in(world, numbered.name, "the task\n" + "".join(lines[1:]), "The task")
    ok(START(capsys, world))
    ok(BASE(capsys, world))
    ok(CHECKS(capsys, world))
    reviewed(capsys, world, kind="full", careful=True, careful_why="customers see it")
    notes = "none\n\n## Migration\n\nnone\n"
    first = ok(propose_with(capsys, world, notes))["result"]
    assert first["careful"]
    assert tip != first["tip"]
    target = numbered.name if same_file else "base.txt"
    moved = ("".join(lines[:-1]) + "the base\n") if same_file else "the base\n"
    world.repo.outside_commit("main", {target: moved.encode()})
    refused(owner(capsys, world), "base")
    ok(START(capsys, world))
    ok(BASE(capsys, world))
    ok(CHECKS(capsys, world))
    assert due(capsys, world) == "propose"
    again = ok(propose_with(capsys, world, notes))["result"]
    assert again["tip"] != first["tip"]
    assert again["pull"]["number"] == first["pull"]["number"]
    assert landing(world)["based"]["reviewed"] == first["tip"]
    assert len(landing(world)["reviews"]) == 1
    assert (world.worktree / numbered.name).read_text().startswith("the task\n")
    assert (world.worktree / target).read_text().endswith("the base\n")


def test_base_keeps_its_rebase_and_approval_after_a_cut_in_the_second_push(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    first = landing(world)["proposed"]
    world.repo.outside_commit("main", {"base.txt": b"Another change landed.\n"})
    refused(owner(capsys, world), "base")
    for step in (START, BASE, CHECKS):
        ok(step(capsys, world))
    before = landing(world)["based"]
    rebase_count = world.acts.done.count("rebase")
    assert due(capsys, world) == "propose"
    world.acts.cut = ("push", 2)
    with pytest.raises(Killed):
        proposal(capsys, world)
    capsys.readouterr()
    tip = head(world)

    refused(BASE(capsys, world), "not-due")
    assert landing(world)["based"] == before
    assert head(world) == tip
    again = ok(proposal(capsys, world))["result"]
    kept = landing(world)
    assert world.acts.done.count("rebase") == rebase_count
    assert world.acts.done.count("push") == 2
    assert (again["tip"], kept["standing"]["tip"]) == (tip, tip)
    assert kept["proposed"]["merge_review"] == "carried"
    assert kept["reads"][-1]["carried_from"] == first["tip"]
    body = world.forge.bodies[again["pull"]["number"]]
    assert "The review carried over the rebase." in body
    assert "The merge review carries over the clean rebase." in body


def test_the_end_of_an_approval_keeps_its_reason_through_two_cut_proposals(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    first = landing(world)["proposed"]["tip"]
    world.repo.outside_commit("main", {"base.txt": b"Another change landed.\n"})
    refused(owner(capsys, world), "base")
    commit_in(world, "extra.txt", "more\n", "fix: one more file")
    for step in (START, BASE, CHECKS):
        ok(step(capsys, world))
    reviewed(capsys, world)
    world.forge.fail_edits = True
    assert proposal(capsys, world)["code"] == 3
    pushed = landing(world)["pushed"]
    assert pushed == head(world) != first
    world.repo.outside_commit("main", {"later.txt": b"A later change landed.\n"})
    for step in (BASE, CHECKS):
        ok(step(capsys, world))
    assert due(capsys, world) == "propose"
    why = (
        f"the rebase started from `{pushed[:9]}`, a tip pushed after the proposal of "
        f"`{first[:9]}`"
    )
    assert proposal(capsys, world)["code"] == 3
    assert why in "".join(one.read_text() for one in world.task_folder.glob("pr-*"))
    assert landing(world)["pushed"] == head(world)
    world.forge.fail_edits = False
    again = ok(proposal(capsys, world))["result"]
    assert again["owner_merge"] == {"state": "ended", "why": why}
    assert why in world.forge.bodies[again["pull"]["number"]]


def test_the_owners_careful_word_on_an_open_pull_request_starts_a_full_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    late_careful(tmp_path, monkeypatch, capsys, reviewer_called_it=False)


def test_the_owners_careful_word_updates_a_proposal_that_is_already_careful(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    late_careful(tmp_path, monkeypatch, capsys, reviewer_called_it=True)


def late_careful(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    *,
    reviewer_called_it: bool,
) -> None:
    """Main's lem-land-review.sh late-care case gives the open request a full review."""
    world = made(tmp_path, monkeypatch)
    notes = "none\n\n## Migration\n\nnone\n"
    if reviewer_called_it:
        upto(capsys, world, "read")
        reviewed(
            capsys, world, kind="full", careful=True, careful_why="customers see it"
        )
        ok(propose_with(capsys, world, notes))
        ok(brief(capsys, world))
        ok(reply(capsys, world))
    else:
        upto(capsys, world, "merge")
    first = landing(world)["pull"]["number"]
    assert "the owner says so" not in world.forge.bodies[first]
    assert due(capsys, world) == "merge"
    note = command(
        "decisions",
        "log",
        "SLUG",
        "--by",
        "owner",
        "--what",
        "whether the task is careful",
        "--chose",
        "careful until its merge",
        "--why",
        "the README is what a customer reads",
    )
    ok(note(capsys, world))
    assert due(capsys, world) == "start"
    refused(owner(capsys, world), "careful-review")
    assert world.forge.merge_calls == []
    ok(START(capsys, world))
    assert (landing(world)["relands"], world.record()["task"]["status"]) == (
        1,
        "landing",
    )
    for verb, step in (("base", BASE), ("checks", CHECKS)):
        if due(capsys, world) == verb:
            ok(step(capsys, world))
    if reviewer_called_it:
        assert due(capsys, world) == "propose"
        assert len(landing(world)["reviews"]) == 1
    else:
        told = ok(review_brief(capsys, world))["result"]
        assert (told["floor"], told["floor_why"]) == (
            "full",
            "the request is careful: the owner says so",
        )
        refused(recorded(capsys, world), "under-floor")
        ok(recorded(capsys, world, kind="full"))
    again = ok(propose_with(capsys, world, notes))["result"]
    assert again["pull"]["number"] == first
    assert (again["careful"], again["who_acts"]) == (True, "owner")
    assert "the owner says so" in world.forge.bodies[first]
    if due(capsys, world) == "merge-review":
        ok(brief(capsys, world))
        ok(reply(capsys, world))
    assert next_step(capsys, world)["result"]["by"] == "owner"
    ok(owner(capsys, world))
    assert [number for number, _ in world.forge.merge_calls] == [first]


def test_a_task_lands_through_a_red_base_kept_whole_by_start(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "checks")
    based = landing(world)["based"]
    # a red base sends the task back to ready, as the checks of `land-checks` do
    state = world.checkout / ".lem" / "state"
    tasks.update(state, SLUG, back_to_ready, world.record()["revision"])
    assert due(capsys, world) == "start"
    ok(START(capsys, world))
    kept = landing(world)
    assert (kept["started"]["round"], kept["based"]) == (1, based)
    assert "round" not in kept
    assert "relands" not in kept
    assert due(capsys, world) == "checks"
    for _, step in JOURNEY[AFTER_BASE:]:
        ok(step(capsys, world))
    assert_landed(world)


def back_to_ready(record: Record) -> Record:
    """The task back in `ready`, its landing as it was."""
    return replace(record, task=replace(record.task, status="ready"))


# Where the journey goes on after `base`.
AFTER_BASE = next(at for at, (verb, _) in enumerate(JOURNEY) if verb == "base") + 1


def test_with_no_command_of_the_checks_start_blocks_the_task_then_takes_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "start")
    settings = world.checkout / ".lem" / "settings.toml"
    settings.write_bytes(SETTINGS.split(b"[checks]")[0])
    said = refused(START(capsys, world), "no-checks")
    assert "the task is blocked" in said["why"]
    assert "checks.commands" in said["fix"]
    task = world.record()["task"]
    assert (task["status"], task["hold"]["kind"]) == ("ready", "blocked")
    refused(START(capsys, world), "no-checks")
    assert (
        len([e for e in world.record()["journal"] if e.get("hold") == "blocked"]) == 1
    )
    settings.write_bytes(SETTINGS)
    ok(START(capsys, world))
    task = world.record()["task"]
    assert (task["status"], task.get("hold")) == ("landing", None)
    assert due(capsys, world) == "base"


def test_a_teammates_commit_on_the_task_branch_is_refused_until_the_branch_holds_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "base")
    run_git(world.worktree, "push", "--quiet", "origin", f"HEAD:refs/heads/{BRANCH}")
    theirs = world.repo.outside_commit(BRANCH, {"THEIRS.md": b"a teammate's line\n"})
    tip = head(world)
    said = refused(BASE(capsys, world), "teammate")
    assert f'{theirs[:9]} "outside: THEIRS.md"' in said["why"]
    assert f"pull --rebase origin {BRANCH}" in said["fix"]
    assert head(world) == tip
    assert "based" not in landing(world)
    assert due(capsys, world) == "base"
    run_git(world.worktree, "pull", "--quiet", "--rebase", "origin", BRANCH)
    based = ok(BASE(capsys, world))["result"]
    assert based["tip"] == head(world)
    assert based["before"] == theirs
    assert (world.worktree / "THEIRS.md").read_text() == "a teammate's line\n"


def conflict_on_main(world: World) -> str:
    """A teammate's edit of the README's one line on origin's main."""
    return world.repo.outside_commit("main", {"README.md": b"The README says hello.\n"})


def resolve_readme(world: World) -> None:
    """The builder rebases onto main and resolves the README's conflict."""
    with pytest.raises(AssertionError):
        run_git(world.worktree, "rebase", "--quiet", "origin/main")
    (world.worktree / "README.md").write_text(README)
    run_git(world.worktree, "add", "README.md")
    run_git(world.worktree, "-c", "core.editor=true", "rebase", "--continue")


def test_a_conflict_with_the_base_is_undone_and_its_resolution_kept_for_a_builder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "base")
    conflict_on_main(world)
    tip = head(world)
    said = refused(BASE(capsys, world), "conflict")
    assert "README.md" in said["why"]
    assert "a builder resolves it" in said["fix"]
    assert head(world) == tip
    assert run_git(world.worktree, "status", "--porcelain") == ""
    assert "based" not in landing(world)
    resolution = landing(world)["resolution"]
    assert resolution == {
        "files": ["README.md"],
        "before": tip,
        "after": tip,
        "base": run_git(world.checkout, "rev-parse", "origin/main"),
    }
    assert due(capsys, world) == "base"
    resolve_readme(world)
    based = ok(BASE(capsys, world))["result"]
    assert based["tip"] == head(world)
    assert based["before"] == head(world)
    kept = landing(world)["resolution"]
    assert (kept["before"], kept["after"]) == (tip, head(world))
    assert due(capsys, world) == "checks"


def test_a_rebase_git_refuses_keeps_nothing_and_gives_gits_words(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "base")
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    hook = hooks / "pre-rebase"
    hook.write_text("#!/bin/sh\necho 'no rebase today' >&2\nexit 1\n")
    hook.chmod(hook.stat().st_mode | stat.S_IXUSR)
    run_git(world.checkout, "config", "core.hooksPath", str(hooks))
    tip = head(world)
    before = world.record()
    said = refused(BASE(capsys, world), "git-refused")
    assert said["why"].startswith(
        "the rebase onto origin/main failed with no file in conflict, and the worktree "
        "is as it was; git said: no rebase today / "
    )
    assert "the owner removes what git names" in said["fix"]
    assert head(world) == tip
    # nothing kept: the mark of the rebase is undone with it
    after = world.record()
    assert (after["task"], after["landing"]) == (before["task"], before["landing"])
    run_git(world.checkout, "config", "--unset", "core.hooksPath")
    ok(BASE(capsys, world))
    assert head(world) != tip
    assert due(capsys, world) == "checks"


@pytest.mark.parametrize("run", ["whole", "cut-after-the-rebase"])
def test_a_rebase_that_drops_a_merge_only_change_is_refused_with_the_tip_before_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    run: str,
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "start")
    # the change sits only in a merge commit of the base into the branch
    base = run_git(world.checkout, "rev-parse", "origin/main")
    run_git(world.worktree, "reset", "--quiet", "--hard", base)
    world.repo.outside_commit("main", {"OTHER.md": b"another note\n"})
    run_git(world.worktree, "fetch", "--quiet", "origin")
    run_git(world.worktree, "merge", "--quiet", "--no-ff", "--no-commit", "origin/main")
    (world.worktree / "README.md").write_text(README)
    run_git(world.worktree, "commit", "--quiet", "--all", "--message", "Merge main")
    world.repo.outside_commit("main", {"MORE.md": b"more\n"})
    ok(START(capsys, world))
    tip = head(world)
    if run != "whole":
        # a stop between the rebase and its record: the tip before it is still named
        world.acts.cut = ("rebase", 1)
        with pytest.raises(Killed):
            BASE(capsys, world)
        capsys.readouterr()
        assert head(world) != tip
    said = refused(BASE(capsys, world), "merge-only")
    assert f"was at {tip}" in said["why"]
    assert f"reset --hard {tip}" in said["fix"]
    assert "dropped ends the task" in said["fix"]
    assert due(capsys, world) == "base"
    again = refused(BASE(capsys, world), "merge-only")
    assert f"reset --hard {tip}" in again["fix"]
    assert world.acts.done.count("rebase") == 1


def conflicting_round(capsys: pytest.CaptureFixture[str], world: World) -> None:
    """The forge wakes a new round and the base step records its conflicts."""
    ok(CONFLICTING(capsys, world))
    kept = landing(world)
    assert (kept["round"], kept["relands"]) == (2, 1)
    assert kept.get("phase", "preparing") == "preparing"
    assert kept["started"]["conflicting"] is True
    again = [e for e in world.record()["journal"] if e["kind"] == "land-again"]
    assert again == [
        {
            "kind": "land-again",
            "at": again[0]["at"],
            "round": 2,
            "relands": 1,
            "conflicting": True,
        }
    ]
    assert world.record()["task"]["status"] == "landing"
    assert due(capsys, world) == "base"
    refused(BASE(capsys, world), "conflict")
    assert landing(world)["resolution"]["files"] == ["README.md"]


def reproposed_conflict(
    capsys: pytest.CaptureFixture[str],
    world: World,
    *,
    case: str,
) -> None:
    """Resolve the forge's conflict and check the account and the approval at proposal."""
    upto(capsys, world, "read")
    if case == "careful":
        reviewed(
            capsys,
            world,
            kind="full",
            careful=True,
            careful_why="customers see the receipt",
        )
        ok(propose_with(capsys, world, "none\n\n## Migration\n\nnone\n"))
    else:
        reviewed(capsys, world)
        ok(proposal(capsys, world))
    ok(brief(capsys, world))
    ok(reply(capsys, world))
    first = landing(world)["proposed"]["tip"]
    assert world.record()["task"]["status"] == "open"
    refused(START(capsys, world), "not-due")
    conflict_on_main(world)
    refused(owner(capsys, world), "base")
    assert landing(world)["standing"]["tip"] == first
    number = landing(world)["pull"]["number"]
    world.forge.conflicting(number)
    conflicting_round(capsys, world)

    resolve_readme(world)
    ok(BASE(capsys, world))
    ok(CHECKS(capsys, world))
    kind = "full" if case == "careful" else "read"
    read = reviewed(
        capsys,
        world,
        kind=kind,
        nit=int(case == "nit"),
        outside=[UNDER] if case == "outside" else [],
    )
    assert read["result"]["of"] == "resolution"
    if case == "outside":
        filed = ok(file_step()(capsys, world))["result"]
        assert [one["path"] for one in filed] == [
            "docs/backlog/the-notes-have-no-date.md"
        ]
        assert head(world) != landing(world)["resolution"]["after"]

    again = ok(proposal(capsys, world))
    kept = landing(world)
    assert again["result"]["pull"]["number"] == number
    line = again["result"]["synced"]
    assert line.startswith(
        "rebased on main after the forge called it conflicting; "
        "one conflict in README.md, resolved by a builder; one read of the resolution"
    )
    assert line.endswith("the checks passed again")
    assert line in again["say"]
    assert f"{line[0].upper()}{line[1:]}." in world.forge.bodies[number].splitlines()
    if case == "outside":
        assert "the merge review carried over the resolved conflict" in line
        assert kept["reads"][-1]["carried_from"] == first
        assert kept["proposed"]["owner_merge"]["state"] == "stands"
        assert kept["standing"]["tip"] == head(world)
    else:
        assert kept["proposed"].get("merge_review") is None
        assert kept["proposed"]["owner_merge"]["state"] == "ended"
        assert "standing" not in kept
        check_one_ended_approval(world)
        assert due(capsys, world) == "merge-review"
        if case == "careful":
            assert "a fresh merge agent reads it: the request is careful" in line


def check_one_ended_approval(world: World) -> None:
    ended = [
        entry["owner_merge"]
        for entry in world.record()["journal"]
        if entry["kind"] == "proposed"
        and entry.get("owner_merge", {}).get("state") == "ended"
    ]
    assert ended == [landing(world)["proposed"]["owner_merge"]]
    assert ended[0]["why"]


def test_a_conflicting_pull_request_wakes_a_new_round_counted_in_relands(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    reproposed_conflict(capsys, made(tmp_path, monkeypatch), case="outside")


@pytest.mark.parametrize("case", ["nit", "careful"])
def test_a_conflict_needs_a_fresh_merge_read_after_a_nit_or_a_careful_call(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    case: str,
) -> None:
    reproposed_conflict(capsys, made(tmp_path, monkeypatch), case=case)


# Each new effect of `start` and `base` on its path, by the act's name and count: the stopped
# rebase is undone before its record, and the record of the block or the conflict is last.
def test_a_cut_after_the_block_of_no_checks_refuses_again_and_writes_nothing_twice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "start")
    settings = world.checkout / ".lem" / "settings.toml"
    settings.write_bytes(SETTINGS.split(b"[checks]")[0])
    revision = world.record()["revision"]
    refused(START(capsys, world), "no-checks")
    assert world.record()["revision"] == revision + 1
    refused(START(capsys, world), "no-checks")
    assert world.record()["revision"] == revision + 1


def test_a_new_round_with_no_checks_waits_and_a_start_over_keeps_the_ended_approval(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    world.repo.outside_commit("main", {"LATER.md": b"one line\n"})
    refused(owner(capsys, world), "base")
    settings = world.checkout / ".lem" / "settings.toml"
    settings.write_bytes(SETTINGS.split(b"[checks]")[0])
    refused(START(capsys, world), "no-checks")
    refused(START(capsys, world), "no-checks")
    assert not landing(world).get("relands")
    settings.write_bytes(SETTINGS)
    ok(START(capsys, world))
    assert landing(world)["relands"] == 1
    assert "standing" in landing(world)
    assert sum(e["kind"] == "land-again" for e in world.record()["journal"]) == 1

    why = "the gate was cut off"
    ok(command("task", "move", "SLUG", "ready", "--start-over", why)(capsys, world))
    settings.write_bytes(SETTINGS.split(b"[checks]")[0])
    stopped = refused(START(capsys, world), "no-checks")
    assert f"The owner's merge ended: the landing started over: {why}" in stopped["why"]
    assert "standing" not in landing(world) and not landing(world).get("reads")
    assert not landing(world).get("reviews")
    assert landing(world)["proposed"]["owner_merge"]["state"] == "ended"
    settings.write_bytes(SETTINGS)
    ok(START(capsys, world))
    assert landing(world)["relands"] == 1


def test_a_start_over_with_no_approval_of_the_owner_names_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    assert "standing" not in landing(world)
    why = "the gate was cut off"
    ok(command("task", "move", "SLUG", "ready", "--start-over", why)(capsys, world))
    settings = world.checkout / ".lem" / "settings.toml"
    settings.write_bytes(SETTINGS.split(b"[checks]")[0])
    stopped = refused(START(capsys, world), "no-checks")
    assert "owner's merge" not in stopped["why"]
    assert "merges it again" not in stopped["why"]
    assert "owner_merge" not in landing(world)["proposed"]


def test_a_builders_conflict_resolution_reapplies_a_commit_the_base_took_out(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path / "a workspace", monkeypatch)
    world.repo.outside_commit("main", {"list.txt": b"a\nb\n", "label.txt": b"old\n"})
    upto(capsys, world, "start")
    ok(START(capsys, world))
    ok(BASE(capsys, world))
    commit_in(world, "list.txt", "a\nb\nc\n", "feat: add the third line")
    original = commit_in(world, "label.txt", "task\n", "feat: change the label")
    world.repo.outside_commit("main", {"list.txt": b"a\nb\nc\n"})
    world.repo.outside_commit("main", {"list.txt": b"a\nb\n", "label.txt": b"base\n"})
    said = refused(BASE(capsys, world), "conflict")
    assert "label.txt" in said["why"]
    assert "rebase --reapply-cherry-picks --empty=drop" in said["fix"]
    assert head(world) == original
    git, where, *rebase = shlex.split(said["fix"].split("`")[1])
    assert (git, where) == ("git", "-C")
    with pytest.raises(AssertionError):
        run_git(Path(rebase[0]), *rebase[1:])
    assert "<<<<<<<" in (world.worktree / "label.txt").read_text()
    (world.worktree / "label.txt").write_text("task\n")
    run_git(world.worktree, "add", "label.txt")
    run_git(world.worktree, "-c", "core.editor=true", "rebase", "--continue")
    resolved = head(world)
    assert (world.worktree / "list.txt").read_text() == "a\nb\nc\n"
    assert ok(BASE(capsys, world))["result"]["tip"] == resolved
    assert head(world) == resolved
    assert landing(world)["resolution"]["files"] == ["label.txt"]


@pytest.mark.parametrize("extra", ["none", "before", "after"])
def test_a_red_base_keeps_the_approval_only_for_the_unchanged_change(
    tmp_path: Path,
    own_home: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    extra: str,
) -> None:
    world = made(tmp_path, monkeypatch)
    settings = world.checkout / ".lem" / "settings.toml"
    settings.write_bytes(
        SETTINGS.replace(b'"grep -q receive README.md"', b'"test -f HEALTHY"')
    )
    world.repo.outside_commit("main", {"HEALTHY": b"yes\n"})
    upto(capsys, world, "merge")
    first = landing(world)["proposed"]["tip"]
    world.repo.outside_commit("main", {"HEALTHY": None})
    refused(owner(capsys, world), "base")
    if extra == "before":
        commit_in(world, "extra.txt", "more\n", "fix: one more file")
    ok(START(capsys, world))
    ok(BASE(capsys, world))
    refused(CHECKS(capsys, world), "red")

    repair = "restore-health"
    subject = "fix: restore health"
    small_built(capsys, world, repair, {"HEALTHY": "restored\n"}, subject)
    ok(command("task", "red-base", "SLUG", "--after", repair)(capsys, world))
    small_landed(capsys, world, repair, subject)
    ok(
        command("task", "move", "SLUG", "ready", "--line", "the base is green again")(
            capsys, world
        )
    )
    ok(START(capsys, world))
    ok(BASE(capsys, world))
    if extra == "after":
        commit_in(world, "extra.txt", "more\n", "fix: one more file")
    ok(CHECKS(capsys, world))
    if extra != "none":
        reviewed(capsys, world)
    proposed = ok(proposal(capsys, world))["result"]
    assert proposed["tip"] != first
    assert landing(world)["relands"] == 1
    carried = proposed["owner_merge"]
    if extra == "none":
        assert carried["state"] == "stands"
        assert len(landing(world)["reviews"]) == 1
        assert len(landing(world)["reads"]) == 2
        assert (
            "The merge review carries over the clean rebase." in world.forge.bodies[1]
        )
        served(world, own_home, monkeypatch)
        ticked(world, own_home, clock.now())
        assert landing(world)["merged"]["via"] == "server"
    else:
        assert run_git(world.worktree, "show", "HEAD:extra.txt") == "more"
        subjects = run_git(world.worktree, "log", "--format=%s", "origin/main..HEAD")
        assert subjects.splitlines().count("fix: one more file") == 1
        assert carried["state"] == "ended"
        assert (
            carried["why"]
            == {
                "after": "the tip changed after the rebase",
                "before": "the previous approval does not cover the change on the new base",
            }[extra]
        )
        assert "standing" not in landing(world)
        assert "The owner's merge ended:" in world.forge.bodies[1]
        changes = [
            e["owner_merge"]
            for e in world.record()["journal"]
            if e["kind"] == "proposed"
            and e.get("owner_merge", {}).get("state") == "ended"
        ]
        assert changes == [carried]


def test_a_cut_after_a_stopped_rebase_is_a_rebase_in_progress_lem_never_aborts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "base")
    conflict_on_main(world)
    tip = head(world)
    world.acts.cut = ("rebase", 1)
    with pytest.raises(Killed):
        BASE(capsys, world)
    capsys.readouterr()
    assert due(capsys, world) == "base"
    said = refused(BASE(capsys, world), "rebase-in-progress")
    assert f"git -C {world.worktree} rebase --abort" in said["fix"]
    assert (world.worktree / "README.md").read_text().startswith("<<<<<<<")
    run_git(world.worktree, "rebase", "--abort")
    assert head(world) == tip
    refused(BASE(capsys, world), "conflict")
    assert landing(world)["resolution"]["before"] == tip


def test_a_cut_after_the_abort_of_a_stopped_rebase_stops_it_again_and_keeps_it_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "base")
    conflict_on_main(world)
    tip = head(world)
    world.acts.cut = ("abort", 1)
    with pytest.raises(Killed):
        BASE(capsys, world)
    capsys.readouterr()
    assert "resolution" not in landing(world)
    assert due(capsys, world) == "base"
    refused(BASE(capsys, world), "conflict")
    assert head(world) == tip
    assert landing(world)["resolution"]["files"] == ["README.md"]
    assert world.acts.done.count("rebase") == 2


def commit_in(world: World, path: str, body: str, subject: str) -> str:
    """A builder's commit of one file in the task's worktree."""
    (world.worktree / path).write_text(body)
    run_git(world.worktree, "add", path)
    run_git(world.worktree, "commit", "--quiet", "--message", subject)
    return head(world)


def polished_at(world: World, after: str) -> None:
    """A polish pass on record whose last commit is `after`, as `land-checks` writes it."""
    state = world.checkout / ".lem" / "state"

    def change(record: Record) -> Record:
        landing_now = record.landing
        assert landing_now is not None
        assert landing_now.started is not None
        made_pass = Polished(before=after, after=after, at=landing_now.started.at)
        return replace(record, landing=replace(landing_now, polished=made_pass))

    tasks.update(state, SLUG, change, world.record()["revision"])


@pytest.mark.parametrize("run", ["whole", "cut-after-the-first-rebase"])
def test_a_second_rebase_never_loses_a_commit_the_first_left_out(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    run: str,
) -> None:
    # main's probe of two rebases (tests/lem-land-shop.sh, mb-probe): a red base repeats the
    # feature's edit, git leaves the feature out of the first rebase, and the base reverts
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "start")
    commit_in(world, "feature.txt", "new\n", "feat: the feature")
    first = commit_in(world, "label.txt", "new\n", "feat: the label")
    ok(START(capsys, world))
    polished_at(world, first)
    red = world.repo.outside_commit(
        "main", {"feature.txt": b"new\n", "broken.txt": b"broken\n"}
    )
    if run != "whole":
        world.acts.cut = ("rebase", 1)
        with pytest.raises(Killed):
            BASE(capsys, world)
        capsys.readouterr()
    ok(BASE(capsys, world))
    subjects = run_git(world.worktree, "log", "--format=%s", "origin/main..HEAD")
    assert "feat: the feature" not in subjects
    assert landing(world)["based"]["before"] == first
    assert "polished" not in landing(world)
    world.repo.outside_commit("main", {"feature.txt": None, "broken.txt": None})
    assert due(capsys, world) == "base"
    said = refused(BASE(capsys, world), "rebase-again")
    assert f"reset --hard {first}" in said["fix"]
    run_git(world.worktree, "reset", "--quiet", "--hard", first)
    ok(BASE(capsys, world))
    assert run_git(world.worktree, "show", "HEAD:feature.txt") == "new"
    assert run_git(world.worktree, "show", "HEAD:label.txt") == "new"
    assert run_git(world.worktree, "merge-base", "--is-ancestor", red, "HEAD") == ""
    assert world.acts.done.count("rebase") == 2
    assert due(capsys, world) == "checks"


@pytest.mark.parametrize("run", ["whole", "cut-after-the-rebase"])
def test_the_rebase_goes_onto_the_base_it_read_though_origin_moves_meanwhile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    run: str,
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "base")
    tip = head(world)
    polished_at(world, tip)
    read = run_git(world.repo.origin, "rev-parse", "main")
    merge_tree, late = git_cli.GitCli.merge_tree, []

    def moving(self: git_cli.GitCli, where: Path, onto: str, made_tip: str) -> object:
        found = merge_tree(self, where, onto, made_tip)
        if not late:
            # another task's fetch moves origin/main between the look and the rebase
            late.append(world.repo.outside_commit("main", {"LATE.md": b"late\n"}))
            run_git(world.checkout, "fetch", "--quiet", "origin")
        return found

    monkeypatch.setattr(git_cli.GitCli, "merge_tree", moving)
    if run != "whole":
        world.acts.cut = ("rebase", 1)
        with pytest.raises(Killed):
            BASE(capsys, world)
        capsys.readouterr()
    else:
        based = ok(BASE(capsys, world))["result"]
        assert based["base"] == read
        assert landing(world)["polished"]["after"] == head(world)
    assert run_git(world.worktree, "merge-base", "--is-ancestor", read, "HEAD") == ""
    assert not (world.worktree / "LATE.md").exists()
    assert due(capsys, world) == "base"
    ok(BASE(capsys, world))
    assert (world.worktree / "LATE.md").is_file()
    assert world.acts.done.count("rebase") == 2
    assert due(capsys, world) == "checks"


def test_a_detached_head_at_the_branchs_own_commit_starts_no_landing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "start")
    run_git(world.worktree, "checkout", "--quiet", "--detach")
    said = refused(START(capsys, world), "off-branch")
    assert f"switch {BRANCH}" in said["fix"]
    assert world.record()["task"]["status"] == "ready"
    run_git(world.worktree, "switch", "--quiet", BRANCH)
    ok(START(capsys, world))
    run_git(world.worktree, "checkout", "--quiet", "--detach")
    tip = head(world)
    refused(BASE(capsys, world), "off-branch")
    assert world.acts.done.count("rebase") == 0
    run_git(world.worktree, "switch", "--quiet", BRANCH)
    assert head(world) == tip
    ok(BASE(capsys, world))


def test_a_rebase_whose_abort_leaves_head_detached_names_it_and_keeps_the_mark(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # main's locked-ref case (tests/lem-land-guards.sh): the lock of the branch's ref held
    # through the rebase's last update of it leaves HEAD detached at the rebased commit
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "base")
    tip = head(world)
    common = run_git(
        world.worktree, "rev-parse", "--path-format=absolute", "--git-common-dir"
    )
    lock = Path(common) / "refs" / "heads" / f"{BRANCH}.lock"
    lock.touch()
    said = refused(BASE(capsys, world), "git-refused")
    lock.unlink()
    moved = head(world)
    assert moved != tip
    assert f"HEAD is detached at {moved[:9]}" in said["why"]
    assert f"`git -C {world.worktree} switch {BRANCH}` puts it back" in said["why"]
    assert "the worktree is as it was" not in said["why"]
    assert landing(world)["based"]["before"] == tip
    run_git(world.worktree, "switch", "--quiet", BRANCH)
    assert head(world) == tip
    ok(BASE(capsys, world))
    assert world.acts.done.count("rebase") == 2


def test_an_abort_that_fails_keeps_no_conflict_and_names_the_rebase_left(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "base")
    conflict_on_main(world)
    tip = head(world)

    def failing(self: git_cli.GitCli, worktree: Path) -> None:
        raise Unanswered("git", "fatal: could not abort")

    monkeypatch.setattr(git_cli.GitCli, "abort", failing)
    said = refused(BASE(capsys, world), "conflict")
    assert "its abort left the worktree not as it was" in said["why"]
    assert f"`git -C {world.worktree} rebase --abort`" in said["why"]
    assert "resolution" not in landing(world)
    monkeypatch.undo()
    run_git(world.worktree, "rebase", "--abort")
    assert head(world) == tip


def test_a_resolution_holds_every_file_a_later_commit_stopped_on(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "checks")
    commit_in(world, "NOTES.md", "our note\n", "docs: our note")
    tip = head(world)
    world.repo.outside_commit(
        "main",
        {"README.md": b"The README says hello.\n", "NOTES.md": b"their note\n"},
    )
    said = refused(BASE(capsys, world), "conflict")
    assert "README.md" in said["why"]
    assert landing(world)["resolution"]["files"] == ["README.md"]
    # the builder resolves each stop of his own rebase
    with pytest.raises(AssertionError):
        run_git(world.worktree, "-c", "core.editor=true", "rebase", "origin/main")
    (world.worktree / "README.md").write_text(README)
    run_git(world.worktree, "add", "README.md")
    with pytest.raises(AssertionError):
        run_git(world.worktree, "-c", "core.editor=true", "rebase", "--continue")
    (world.worktree / "NOTES.md").write_text("our note\n")
    run_git(world.worktree, "add", "NOTES.md")
    run_git(world.worktree, "-c", "core.editor=true", "rebase", "--continue")
    ok(BASE(capsys, world))
    resolution = landing(world)["resolution"]
    assert resolution["files"] == ["NOTES.md", "README.md"]
    assert (resolution["before"], resolution["after"]) == (tip, head(world))


def test_a_conflict_resolution_accepts_non_utf8_content_and_commit_subject(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "base")
    conflict_on_main(world)
    refused(BASE(capsys, world), "conflict")
    with pytest.raises(AssertionError):
        run_git(world.worktree, "rebase", "origin/main")
    (world.worktree / "README.md").write_bytes(b"The README says caf\xe9.\n")
    run_git(world.worktree, "add", "README.md")
    subject = tmp_path / "subject"
    subject.write_bytes(b"docs: caf\xe9\n")
    run_git(
        world.worktree,
        "-c",
        "i18n.commitEncoding=ISO-8859-1",
        "commit",
        "--quiet",
        "-F",
        str(subject),
    )
    run_git(world.worktree, "rebase", "--continue")

    ok(BASE(capsys, world))
    resolution = landing(world)["resolution"]
    assert resolution["files"] == ["README.md"]
    assert resolution["after"] == head(world)
    assert (world.worktree / "README.md").read_bytes() == b"The README says caf\xe9.\n"


def test_a_resolution_names_unicode_and_changed_binary_paths_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    world.repo.outside_commit(
        "main", {"change.bin": b"\0before", "keep.bin": b"\0before"}
    )
    upto(capsys, world, "checks")
    files = {"café.txt": b"Ours\n", "change.bin": b"\0ours", "keep.bin": b"\0ours"}
    for name, body in files.items():
        (world.worktree / name).write_bytes(body)
    run_git(world.worktree, "add", "--", *files)
    run_git(world.worktree, "commit", "--quiet", "-m", "docs: add the examples")
    world.repo.outside_commit(
        "main",
        {
            "README.md": b"The README says hello.\n",
            "café.txt": b"Theirs\n",
            "change.bin": b"\0theirs",
        },
    )
    refused(BASE(capsys, world), "conflict")
    assert landing(world)["resolution"]["files"] == ["README.md"]

    with pytest.raises(AssertionError):
        run_git(world.worktree, "-c", "core.editor=true", "rebase", "origin/main")
    (world.worktree / "README.md").write_text(README)
    run_git(world.worktree, "add", "--", "README.md")
    with pytest.raises(AssertionError):
        run_git(world.worktree, "-c", "core.editor=true", "rebase", "--continue")
    (world.worktree / "café.txt").write_text("Resolved\n")
    (world.worktree / "change.bin").write_bytes(b"\0resolved")
    run_git(world.worktree, "add", "--", "café.txt", "change.bin")
    run_git(world.worktree, "-c", "core.editor=true", "rebase", "--continue")

    ok(BASE(capsys, world))
    assert landing(world)["resolution"]["files"] == [
        "README.md",
        "café.txt",
        "change.bin",
    ]
    assert (world.worktree / "keep.bin").read_bytes() == b"\0ours"


def test_a_conflict_wake_never_starts_a_round_over_a_merge_call_on_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    world.acts.cut = ("write:intent", 1)
    with pytest.raises(Killed):
        command("land", "merge", "SLUG", "--by", "merger", "--message", "fix")(
            capsys, world
        )
    capsys.readouterr()
    world.forge.conflicting(landing(world)["pull"]["number"])
    said = refused(CONFLICTING(capsys, world), "not-due")
    assert "reconciled first" in said["why"]
    kept = landing(world)
    assert (kept.get("phase"), kept.get("relands", 0)) == ("open", 0)
    assert kept["intent"] is not None
    assert world.forge.merge_calls == []


def test_a_remote_task_branch_the_base_holds_is_no_teammates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "base")
    on_main = run_git(world.repo.origin, "rev-parse", "main")
    run_git(world.repo.origin, "update-ref", f"refs/heads/{BRANCH}", on_main)
    ok(BASE(capsys, world))
    assert due(capsys, world) == "checks"
