"""The hard paths of the landing's start and base (`landing.md` E, proof owner `land-base`), each
a journey on a real repository and `LocalForge`, through the tree in this process with `--repo`
to the test's own repository, as `tests/journeys/test_skeleton.py` runs the plain path.

Recovery, no checks, a teammate's commit, a conflict with the base, a rebase git refuses, a
merge-only change, a conflicting pull request on the forge and the count of relands; and a cut
after each new effect of `start` and `base`, after which the step is due again and does nothing
twice.
"""

import stat
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from fakes.repo import run_git
from journeys.test_skeleton import (
    BRANCH,
    JOURNEY,
    SETTINGS,
    SLUG,
    Envelope,
    Killed,
    World,
    assert_landed,
    command,
    made,
    next_step,
    parses,
    upto,
)
from lem.adapters import git_cli
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
    # the builder resolves it in the worktree
    stopped = ["-c", "core.editor=true", "rebase", "--quiet", "origin/main"]
    with pytest.raises(AssertionError):
        run_git(world.worktree, *stopped)
    (world.worktree / "README.md").write_text(README)
    run_git(world.worktree, "add", "README.md")
    run_git(world.worktree, "-c", "core.editor=true", "rebase", "--continue")
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


def test_a_conflicting_pull_request_wakes_a_new_round_counted_in_relands(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge-review")
    assert world.record()["task"]["status"] == "open"
    conflict_on_main(world)
    number = landing(world)["pull"]["number"]
    world.forge.conflicting(number)
    refused(command("land", "start", "SLUG")(capsys, world), "not-due")
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
