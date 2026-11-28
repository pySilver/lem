"""The `git` adapter (`lem.adapters.git_cli`) against the `Git` port's whole contract, on a real
repository, and the adapter's own cases: the names of a conflict as git wrote them, git's words
when it refuses a rebase, and a git with no `merge-tree --write-tree`."""

import os
import stat
import subprocess
import unicodedata
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest

from contract.suites.git import FILES, GitContract, commit_file, task_worktree
from fakes.repo import RealRepo, git_env, run_git, write
from lem.adapters import git_cli, git_cli_acts, git_cli_shell
from lem.adapters.git_cli_names import shown
from lem.ports.faults import Unanswered
from lem.ports.git_facts import LEASE, Conflict, GitRefused
from lem.ports.place import Place

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


@dataclass(frozen=True)
class RealWorld:
    """A real repository with its origin, its main checkout and a folder for worktrees."""

    git: git_cli.GitCli
    repo: RealRepo
    worktrees: Path

    @property
    def checkout(self) -> Path:
        return self.repo.checkout

    def outside_commit(
        self, branch: str, files: dict[str, bytes | None], start: str = "main"
    ) -> str:
        return self.repo.outside_commit(branch, files, start)

    def merge_in(self, where: Path, ref: str, files: dict[str, bytes]) -> str:
        run_git(where, "merge", "--quiet", "--no-ff", "--no-commit", ref)
        write(where, dict(files))
        run_git(where, "add", "--all")
        run_git(where, "commit", "--quiet", "--message", f"Merge {ref}")
        return run_git(where, "rev-parse", "HEAD")

    def resolve(self, where: Path, files: dict[str, bytes]) -> str:
        write(where, dict(files))
        run_git(where, "add", "--all")
        run_git(where, "commit", "--quiet", "--no-edit")
        return run_git(where, "rev-parse", "HEAD")

    def refuse_commits(self, said: str) -> None:
        hook = self.checkout / ".git" / "hooks" / "pre-commit"
        hook.parent.mkdir(parents=True, exist_ok=True)
        hook.write_text(f"#!/bin/sh\necho '{said}' >&2\nexit 1\n")
        hook.chmod(0o755)

    def ignore(self, path: str) -> None:
        exclude = self.checkout / ".git" / "info" / "exclude"
        with exclude.open("a", encoding="utf-8") as rules:
            rules.write(f"\n/{path}\n")

    def after_reset_tip_check(
        self, patch: pytest.MonkeyPatch, act: Callable[[], None]
    ) -> None:
        clean = git_cli_acts.clean

        def checked(shell: git_cli_shell.Shell, folder: Path) -> bool:
            found = clean(shell, folder)
            act()
            return found

        patch.setattr(git_cli_acts, "clean", checked)


def real_world(folder: Path, environ: dict[str, str] | None = None) -> RealWorld:
    """A repository of `FILES` on `main`, pushed and fetched, and git with the test's
    environment, or `environ`."""
    repo = RealRepo.init(folder, dict(FILES))
    place = Place(
        checkout=repo.checkout, home=folder / "home", environ=environ or git_env()
    )
    return RealWorld(git=git_cli.bind(place), repo=repo, worktrees=folder / "worktrees")


class TestGitCli(GitContract):
    def world(self, folder: Path) -> RealWorld:
        return real_world(folder)


def test_reset_refuses_an_ignored_file_at_an_alias_of_the_target(
    tmp_path: Path,
) -> None:
    world = real_world(tmp_path)
    where = task_worktree(world)
    target = commit_file(world, where, "ENV", b"tracked\n")
    (where / "ENV").unlink()
    current = world.git.commit(where, "remove ENV", ("ENV",))
    assert isinstance(current, str), current
    world.ignore("env")
    local = where / "env"
    local.write_bytes(b"local only\n")
    if not (where / "ENV").exists():
        pytest.skip("the file system distinguishes these names")
    assert world.git.clean(where)
    refused = world.git.reset(where, target, current)
    assert isinstance(refused, GitRefused), refused
    assert local.read_bytes() == b"local only\n"
    assert world.git.tip(where, "HEAD") == current


@pytest.mark.parametrize("subject", ["change a", "change a\u2028with a note"])
def test_history_keeps_tabs_in_the_author_and_line_separators_in_the_subject(
    tmp_path: Path, subject: str
) -> None:
    author = "Ada\tLovelace"
    world = real_world(tmp_path, {**git_env(), "GIT_AUTHOR_NAME": author})
    where = task_worktree(world)
    base = world.git.tip(where, "HEAD")
    assert base is not None
    write(where, {"a.txt": b"a\n"})
    tip = world.git.commit(where, subject, ("a.txt",))
    assert isinstance(tip, str), tip
    commit_file(world, where, "b.txt", b"b\n")
    commits = world.git.commits(where, base, "HEAD")
    assert [(one.sha, one.author, one.subject) for one in commits] == [
        (tip, author, subject),
        (world.git.tip(where, "HEAD"), author, "change b.txt"),
    ]
    world.outside_commit("main", {"a.txt": b"a\n"})
    world.git.fetch(where)
    assert world.git.left_out(where, "origin/main", "HEAD") == commits[:1]


def test_a_commit_refusal_uses_stdout_when_git_has_no_stderr(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    world = real_world(tmp_path)
    where = task_worktree(world)
    write(where, {"a.txt": b"a\n"})
    tried = git_cli_shell.Shell.tried

    def refuse_commit(
        shell: git_cli_shell.Shell, folder: Path, *args: str
    ) -> subprocess.CompletedProcess[str]:
        if args[0] == "commit":
            return subprocess.CompletedProcess(args, 1, "use a backlog subject\n", "")
        return tried(shell, folder, *args)

    monkeypatch.setattr(git_cli_shell.Shell, "tried", refuse_commit)
    refused = world.git.commit(where, "add a", ("a.txt",))
    assert refused == GitRefused(said="use a backlog subject")


def test_a_checkout_on_another_branch_at_the_same_commit_does_not_follow(
    tmp_path: Path,
) -> None:
    world = real_world(tmp_path)
    run_git(world.checkout, "checkout", "--quiet", "-b", "other")
    before = run_git(world.checkout, "rev-parse", "other")
    world.outside_commit("main", {"other.txt": b"o\n"})
    world.git.fetch(world.checkout)
    refused = world.git.fast_forward(world.checkout, "origin/main")
    assert isinstance(refused, GitRefused)
    assert "not on main" in refused.said
    assert run_git(world.checkout, "rev-parse", "other") == before


def unmerged(where: Path, names: tuple[bytes, ...]) -> None:
    """An index in `where` that holds each of `names` unmerged, as a stopped rebase leaves
    it. The index takes a name that is not UTF-8, which APFS refuses as a file."""
    blob = subprocess.run(
        ["git", "-C", str(where), "hash-object", "-w", "--stdin"],
        input=b"x\n",
        capture_output=True,
        env=git_env(),
        check=True,
    ).stdout.strip()
    rows = (
        b"100644 %s %d\t%s\0" % (blob, stage, name)
        for name in names
        for stage in (1, 2, 3)
    )
    subprocess.run(
        ["git", "-C", str(where), "update-index", "-z", "--index-info"],
        input=b"".join(rows),
        env=git_env(),
        check=True,
    )


@pytest.mark.parametrize("quote", ["true", "false"])
def test_the_files_of_a_stopped_rebase_are_named_as_git_wrote_them(
    tmp_path: Path, quote: str
) -> None:
    world = real_world(tmp_path)
    where = task_worktree(world)
    commit_file(world, where, "README.md", b"ours\n")
    world.outside_commit("main", {"README.md": b"theirs\n"})
    world.git.fetch(where)
    assert world.git.rebase(where, "origin/main", reapply=False) == Conflict(
        files=("README.md",)
    )
    run_git(where, "config", "core.quotePath", quote)
    unmerged(where, ("café.txt".encode(), b"caf\xe9.txt", b"a\nb.txt", b"e\x1b[1m"))
    state = world.git.rebase_state(where)
    assert state is not None
    assert state.files == (
        "README.md",
        "a<U+000A>b.txt",
        "caf<0xE9>.txt",
        "café.txt",
        "e<U+001B>[1m",
    )


def test_two_paths_never_share_a_shown_name_and_none_breaks_a_line() -> None:
    raws = (
        b"a\nb.txt",
        b"a\tb.txt",
        b"a<U+000A>b.txt",
        "a\u202eb.txt".encode(),
        "a\u2028b.txt".encode(),
        "a\u2029b.txt".encode(),
        b"a\xe9b.txt",
        b"a\xe8b.txt",
        b"a<0xE9>b.txt",
    )
    names = [shown(raw) for raw in raws]
    assert len(set(names)) == len(raws)
    unshown = {"Cc", "Cf", "Zl", "Zp"}
    assert not [
        name
        for name in names
        if any(unicodedata.category(char) in unshown for char in name)
    ]


def test_a_merge_tree_conflict_names_its_files_as_shown(tmp_path: Path) -> None:
    world = real_world(tmp_path)
    where = task_worktree(world)
    tip = commit_file(world, where, "a\nb.txt", b"ours\n")
    world.outside_commit("main", {"a\nb.txt": b"theirs\n"})
    world.git.fetch(where)
    assert world.git.merge_tree(where, "origin/main", tip) == Conflict(
        files=("a<U+000A>b.txt",)
    )


def test_a_resolution_git_staged_by_itself_waits_for_a_builder(tmp_path: Path) -> None:
    world = real_world(tmp_path)
    where = task_worktree(world)
    commit_file(world, where, "README.md", b"ours\n")
    world.outside_commit("main", {"README.md": b"theirs\n"})
    world.git.fetch(where)
    assert isinstance(world.git.rebase(where, "origin/main", reapply=False), Conflict)
    # what `rerere.autoupdate` leaves: the file resolved and staged, none unmerged
    (where / "README.md").write_bytes(b"resolved\n")
    run_git(where, "add", "README.md")
    state = world.git.rebase_state(where)
    assert state is not None
    assert state.files == ("README.md",)


def test_a_rebase_a_hook_refuses_gives_each_line_git_said(tmp_path: Path) -> None:
    world = real_world(tmp_path)
    where = task_worktree(world)
    tip = commit_file(world, where, "a.txt", b"a\n")
    world.outside_commit("main", {"other.txt": b"o\n"})
    world.git.fetch(where)
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    hook = hooks / "pre-rebase"
    hook.write_text("#!/bin/sh\necho 'no rebase today' >&2\nexit 1\n")
    hook.chmod(hook.stat().st_mode | stat.S_IXUSR)
    run_git(world.checkout, "config", "core.hooksPath", str(hooks))
    refused = world.git.rebase(where, "origin/main", reapply=False)
    assert isinstance(refused, GitRefused)
    assert refused.said.startswith("no rebase today / ")
    assert "pre-rebase hook refused to rebase" in refused.said
    assert world.git.rebase_state(where) is None
    assert world.git.tip(where, "HEAD") == tip


def test_a_git_with_no_write_tree_is_a_fault_that_names_its_version(
    tmp_path: Path,
) -> None:
    # git 2.37 knows no `merge-tree --write-tree`: it prints its usage, exit 129
    stand_in = tmp_path / "bin"
    stand_in.mkdir()
    script = stand_in / "git"
    script.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        "  *--version*) echo 'git version 2.37.0' ;;\n"
        '  *) echo "error: unknown option \\`write-tree\'" >&2; exit 129 ;;\n'
        "esac\n"
    )
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    environ = {**git_env(), "PATH": f"{stand_in}{os.pathsep}{os.environ['PATH']}"}
    world = real_world(tmp_path / "repo", environ)
    with pytest.raises(Unanswered) as raised:
        world.git.merge_tree(world.checkout, "a" * 40, "b" * 40)
    said = raised.value.said
    assert "needs git 2.38 or newer" in said
    assert "says git version 2.37.0" in said
    assert "the owner updates git" in said


def stand_in(folder: Path, body: str) -> dict[str, str]:
    """An environment whose `git` is a stand-in script of `body`, first on the path."""
    folder.mkdir(parents=True, exist_ok=True)
    script = folder / "git"
    script.write_text(f"#!/bin/sh\n{body}\n")
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    return {**git_env(), "PATH": f"{folder}{os.pathsep}{os.environ['PATH']}"}


def adapter(tmp_path: Path, body: str) -> git_cli.GitCli:
    """The adapter with a stand-in git of `body`."""
    environ = stand_in(tmp_path / "bin", body)
    return git_cli.bind(
        Place(checkout=tmp_path, home=tmp_path / "home", environ=environ)
    )


def test_git_reads_nothing_on_its_standard_input(tmp_path: Path) -> None:
    git = adapter(tmp_path, f'cat > "{tmp_path}/read"; echo done')
    assert git.said(tmp_path, "status") == "done"
    assert (tmp_path / "read").read_bytes() == b""


def test_a_run_is_given_back_whole_and_only_said_raises_on_a_failure(
    tmp_path: Path,
) -> None:
    git = adapter(tmp_path, "echo out; echo first >&2; echo last >&2; exit 3")
    ran = git.tried(tmp_path, "status")
    assert (ran.returncode, ran.stdout, ran.stderr) == (3, "out\n", "first\nlast\n")
    with pytest.raises(Unanswered) as raised:
        git.said(tmp_path, "status")
    assert raised.value.said == "last"
    assert git.commit_at(tmp_path, "HEAD") is None


def test_a_git_that_runs_past_its_limit_is_a_fault(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(git_cli_shell, "TIMEOUT", 0.2)
    git = adapter(tmp_path, "exec sleep 5")
    with pytest.raises(Unanswered, match="timed out"):
        git.tried(tmp_path, "fetch")


def test_a_merge_tree_puts_the_base_first_as_the_rebase_does(tmp_path: Path) -> None:
    # a `merge=union` file keeps both sides' lines, the first side's first: the order of
    # merge_tree's arguments is the rebase's only when the base comes first
    world = real_world(tmp_path)
    write(
        world.checkout,
        {".gitattributes": b"notes.txt merge=union\n", "notes.txt": b"0\n"},
    )
    run_git(world.checkout, "add", "--all")
    run_git(world.checkout, "commit", "--quiet", "--message", "notes")
    run_git(world.checkout, "push", "--quiet", "origin", "main")
    where = task_worktree(world)
    tip = commit_file(world, where, "notes.txt", b"0\nours\n")
    world.outside_commit("main", {"notes.txt": b"0\ntheirs\n"})
    world.git.fetch(where)
    foreseen = world.git.merge_tree(where, "origin/main", tip)
    reversed_order = world.git.merge_tree(where, tip, "origin/main")
    assert foreseen != reversed_order
    rebased = world.git.rebase(where, "origin/main", reapply=False)
    assert isinstance(rebased, str)
    assert world.git.tree(where, rebased) == foreseen
    assert world.git.show(where, rebased, "notes.txt") == b"0\ntheirs\nours\n"


def test_a_detached_head_is_on_no_branch_and_a_checkout_with_no_origin_names_none(
    tmp_path: Path,
) -> None:
    world = real_world(tmp_path)
    where = task_worktree(world)
    run_git(where, "checkout", "--quiet", "--detach")
    assert world.git.branch_of(where) is None
    run_git(world.checkout, "remote", "remove", "origin")
    assert world.git.origin_url(world.checkout) is None


def test_a_merge_whose_commit_a_hook_refuses_leaves_no_merge_behind(
    tmp_path: Path,
) -> None:
    world = real_world(tmp_path)
    where = task_worktree(world)
    tip = commit_file(world, where, "a.txt", b"a\n")
    theirs = world.outside_commit("main", {"other.txt": b"o\n"})
    world.git.fetch(where)
    hook = world.checkout / ".git" / "hooks" / "pre-merge-commit"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/bin/sh\necho 'no merge today' >&2\nexit 1\n")
    hook.chmod(0o755)
    refused = world.git.merge(where, theirs, "Merge origin/main")
    assert isinstance(refused, GitRefused)
    assert "no merge today" in refused.said
    assert world.git.tip(where, "HEAD") == tip
    assert world.git.tip(where, "MERGE_HEAD") is None
    assert world.git.clean(where)


@pytest.mark.parametrize("body", [b"resolved\n", b"ours\n"])
def test_a_merge_over_a_builders_merge_in_progress_is_refused_and_aborts_nothing(
    tmp_path: Path, body: bytes
) -> None:
    world = real_world(tmp_path)
    where = task_worktree(world)
    tip = commit_file(world, where, "README.md", b"ours\n")
    theirs = world.outside_commit("main", {"README.md": b"theirs\n"})
    world.git.fetch(where)
    assert world.git.merge_head(where) is None
    assert world.git.merge(where, theirs, "Merge origin/main") == Conflict(
        files=("README.md",)
    )
    # the builder resolves and stages, and commits nothing; "ours" leaves HEAD's tree
    (where / "README.md").write_bytes(body)
    run_git(where, "add", "--all")
    assert world.git.merge_head(where) == theirs
    again = world.git.merge(where, theirs, "Merge origin/main")
    assert isinstance(again, GitRefused)
    assert "MERGE_HEAD" in again.said
    assert world.git.merge_head(where) == theirs
    assert world.git.tip(where, "HEAD") == tip
    assert (where / "README.md").read_bytes() == body


def test_a_push_whose_lease_git_refuses_after_the_read_says_stale_info(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    world = real_world(tmp_path)
    where = task_worktree(world)
    first = commit_file(world, where, "a.txt", b"a\n")
    assert world.git.push(where, "fix-the-login", None, commit=first) == first
    world.outside_commit("fix-the-login", {"t.txt": b"t\n"})
    second = commit_file(world, where, "a.txt", b"aa\n")
    # origin moves between the adapter's read of it and the push itself
    monkeypatch.setattr(git_cli_acts.Rewrite, "on_origin", lambda *_: first)
    refused = world.git.push(where, "fix-the-login", first, commit=second)
    assert isinstance(refused, GitRefused)
    assert refused.said.startswith(f"{LEASE}: ")


def test_a_push_a_hook_refuses_is_no_lease_refusal(tmp_path: Path) -> None:
    world = real_world(tmp_path)
    where = task_worktree(world)
    first = commit_file(world, where, "a.txt", b"a\n")
    hook = world.checkout / ".git" / "hooks" / "pre-push"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/bin/sh\necho 'no push today' >&2\nexit 1\n")
    hook.chmod(0o755)
    refused = world.git.push(where, "fix-the-login", None, commit=first)
    assert isinstance(refused, GitRefused)
    assert not refused.said.startswith(LEASE)


def test_a_conflict_whose_resolution_rerere_staged_waits_for_a_builder(
    tmp_path: Path,
) -> None:
    world = real_world(tmp_path)
    run_git(world.checkout, "config", "rerere.enabled", "true")
    run_git(world.checkout, "config", "rerere.autoupdate", "true")
    where = task_worktree(world)
    tip = commit_file(world, where, "README.md", b"ours\n")
    theirs = world.outside_commit("main", {"README.md": b"theirs\n"})
    world.git.fetch(where)
    first = world.git.merge(where, theirs, "Merge origin/main")
    assert first == Conflict(files=("README.md",))
    world.resolve(where, {"README.md": b"resolved\n"})
    run_git(where, "reset", "--quiet", "--hard", tip)
    # git stages the resolution it recorded, and leaves no file unmerged
    again = world.git.merge(where, theirs, "Merge origin/main")
    assert again == Conflict(files=("README.md",))
    assert world.git.tip(where, "MERGE_HEAD") == theirs
    assert (where / "README.md").read_bytes() == b"resolved\n"
    run_git(where, "commit", "--quiet", "--no-edit")
    assert world.git.commits(where, tip, "HEAD")[-1].parents == (tip, theirs)
