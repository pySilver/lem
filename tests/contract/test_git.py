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
from lem.adapters import git_cli
from lem.adapters.git_cli_names import shown
from lem.ports.faults import Unanswered
from lem.ports.git_facts import Conflict, GitRefused
from lem.ports.place import Place

if TYPE_CHECKING:
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
