"""The contract of the `Git` port: what every implementation does, `ModelGit` now and the
`git` adapter when `land-base` builds it.

A test file subclasses `GitContract` as `Test...` and gives `world`: a repository with one
commit of `README.md` on `main`, pushed and fetched, its main checkout, a folder for worktrees,
and a hand that pushes a commit as someone else.
"""

from typing import TYPE_CHECKING, Protocol

import pytest

from lem.ports.git_facts import Conflict, GitRefused

if TYPE_CHECKING:
    from pathlib import Path

    from lem.ports.git import Git

FILES = {"README.md": b"one\ntwo\nthree\n"}


class GitWorld(Protocol):
    """A repository for one case."""

    @property
    def git(self) -> Git: ...
    @property
    def checkout(self) -> Path: ...
    @property
    def worktrees(self) -> Path: ...

    def outside_commit(
        self, branch: str, files: dict[str, bytes | None], start: str = "main"
    ) -> str: ...


def task_worktree(world: GitWorld, name: str = "fix-the-login") -> Path:
    """A worktree of a task branch, cut from `main`."""
    path = world.worktrees / name
    world.git.worktree_add(world.checkout, path, name, "main")
    return path


def commit_file(world: GitWorld, where: Path, path: str, body: bytes) -> str:
    """Write and commit one file in a worktree."""
    (where / path).write_bytes(body)
    return world.git.commit(where, f"change {path}", (path,))


class GitContract:
    """The cases every implementation of `Git` passes."""

    def world(self, folder: Path) -> GitWorld:
        """A fresh repository in `folder`."""
        raise NotImplementedError

    def test_a_commit_moves_the_tip_and_its_file_reads_back(
        self, tmp_path: Path
    ) -> None:
        world = self.world(tmp_path)
        where = task_worktree(world)
        before = world.git.tip(where, "HEAD")
        assert world.git.clean(where)
        (where / "a.txt").write_bytes(b"a\n")
        assert not world.git.clean(where)
        made = world.git.commit(where, "add a", ("a.txt",))
        assert world.git.clean(where)
        assert world.git.tip(where, "HEAD") == made
        assert len(made) == 40
        assert world.git.show(where, made, "a.txt") == b"a\n"
        assert world.git.show(where, made, "gone.txt") is None
        assert before is not None
        assert world.git.tree(where, made) != world.git.tree(where, before)
        assert world.git.main_checkout(where) == world.checkout

    def test_history_facts_name_the_range_the_ancestry_and_the_size(
        self, tmp_path: Path
    ) -> None:
        world = self.world(tmp_path)
        where = task_worktree(world)
        base = world.git.tip(where, "main")
        assert base is not None
        first = commit_file(world, where, "a.txt", b"a\n")
        second = commit_file(world, where, "b.txt", b"b\nb\n")
        listed = world.git.commits(where, base, second)
        assert [(c.sha, c.subject) for c in listed] == [
            (first, "change a.txt"),
            (second, "change b.txt"),
        ]
        assert world.git.is_ancestor(where, base, second)
        assert not world.git.is_ancestor(where, second, base)
        assert world.git.merge_base(where, second, "main") == base
        stat = world.git.diff_stat(where, base, second)
        assert (stat.paths, stat.added, stat.removed) == (("a.txt", "b.txt"), 3, 0)

    def test_fetch_brings_what_someone_else_pushed(self, tmp_path: Path) -> None:
        world = self.world(tmp_path)
        before = world.git.remote_head(world.checkout, "main")
        pushed = world.outside_commit("main", {"other.txt": b"o\n"})
        assert world.git.remote_head(world.checkout, "main") == before
        world.git.fetch(world.checkout)
        assert world.git.remote_head(world.checkout, "main") == pushed
        assert world.git.tip(world.checkout, "origin/main") == pushed

    def test_a_clean_rebase_gives_the_tree_merge_tree_named(
        self, tmp_path: Path
    ) -> None:
        world = self.world(tmp_path)
        where = task_worktree(world)
        reviewed = commit_file(world, where, "a.txt", b"a\n")
        world.outside_commit("main", {"other.txt": b"o\n"})
        world.git.fetch(where)
        foreseen = world.git.merge_tree(where, "origin/main", reviewed)
        rebased = world.git.rebase(where, "origin/main", reapply=False)
        assert isinstance(rebased, str)
        assert rebased != reviewed
        assert world.git.tree(where, rebased) == foreseen
        assert world.git.is_ancestor(where, "origin/main", rebased)
        assert world.git.rebase_state(where) is None

    def test_a_conflicting_rebase_stops_and_its_abort_restores_the_tip(
        self, tmp_path: Path
    ) -> None:
        world = self.world(tmp_path)
        where = task_worktree(world)
        tip = commit_file(world, where, "README.md", b"ours\n")
        world.outside_commit("main", {"README.md": b"theirs\n"})
        world.git.fetch(where)
        foreseen = world.git.merge_tree(where, "origin/main", tip)
        assert isinstance(foreseen, Conflict)
        assert foreseen.files == ("README.md",)
        stopped = world.git.rebase(where, "origin/main", reapply=False)
        assert stopped == Conflict(files=("README.md",))
        state = world.git.rebase_state(where)
        assert state is not None
        assert state.files == ("README.md",)
        world.git.abort(where)
        assert world.git.rebase_state(where) is None
        assert world.git.tip(where, "HEAD") == tip
        assert world.git.clean(where)

    def test_a_push_carries_a_lease_on_the_commit_lem_pushed_last(
        self, tmp_path: Path
    ) -> None:
        world = self.world(tmp_path)
        where = task_worktree(world)
        first = commit_file(world, where, "a.txt", b"a\n")
        assert world.git.push(where, "fix-the-login", None) == first
        again = world.git.push(where, "fix-the-login", None)
        assert isinstance(again, GitRefused)
        second = commit_file(world, where, "a.txt", b"aa\n")
        assert world.git.push(where, "fix-the-login", first) == second
        teammate = world.outside_commit("fix-the-login", {"t.txt": b"t\n"})
        third = commit_file(world, where, "a.txt", b"aaa\n")
        refused = world.git.push(where, "fix-the-login", second)
        assert isinstance(refused, GitRefused)
        world.git.fetch(where)
        assert world.git.remote_head(where, "fix-the-login") == teammate
        assert world.git.tip(where, "HEAD") == third

    def test_a_branch_is_deleted_only_at_the_commit_named(self, tmp_path: Path) -> None:
        world = self.world(tmp_path)
        where = task_worktree(world)
        tip = commit_file(world, where, "a.txt", b"a\n")
        world.git.worktree_remove(world.checkout, where)
        assert not where.exists()
        base = world.git.tip(world.checkout, "main")
        assert base is not None
        assert not world.git.branch_delete(world.checkout, "fix-the-login", base)
        assert world.git.tip(world.checkout, "fix-the-login") == tip
        assert world.git.branch_delete(world.checkout, "fix-the-login", tip)
        assert world.git.tip(world.checkout, "fix-the-login") is None

    def test_the_base_checkout_follows_only_by_a_fast_forward(
        self, tmp_path: Path
    ) -> None:
        world = self.world(tmp_path)
        pushed = world.outside_commit("main", {"other.txt": b"o\n"})
        world.git.fetch(world.checkout)
        assert world.git.fast_forward(world.checkout, "origin/main") == pushed
        assert (world.checkout / "other.txt").read_bytes() == b"o\n"
        (world.checkout / "mine.txt").write_bytes(b"m\n")
        world.git.commit(world.checkout, "a local commit", ("mine.txt",))
        world.outside_commit("main", {"more.txt": b"m\n"})
        world.git.fetch(world.checkout)
        assert isinstance(
            world.git.fast_forward(world.checkout, "origin/main"), GitRefused
        )

    def test_an_existing_worktree_path_is_a_fault(self, tmp_path: Path) -> None:
        world = self.world(tmp_path)
        task_worktree(world)
        with pytest.raises(Exception, match="already exists"):
            task_worktree(world)
