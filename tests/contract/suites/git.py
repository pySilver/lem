"""The contract of the `Git` port: what every implementation does, `ModelGit` now and the
`git` adapter when `land-base` builds it.

A test file subclasses `GitContract` as `Test...` and gives `world`: a repository with one
commit of `README.md` on `main`, pushed and fetched, its main checkout, a folder for worktrees,
a hand that pushes a commit as someone else (the teammate, by name), one that makes a merge
commit in a worktree (`git merge --no-ff`, with files edited in the merge itself), one that
commits a merge that stopped on a conflict with the files as a builder resolved them, and one
that puts a commit hook in place that refuses every commit.
"""

from typing import TYPE_CHECKING, Protocol

import pytest

from lem.ports.git_facts import Conflict, GitRefused

if TYPE_CHECKING:
    from collections.abc import Callable
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
    def merge_in(self, where: Path, ref: str, files: dict[str, bytes]) -> str: ...
    def resolve(self, where: Path, files: dict[str, bytes]) -> str: ...
    def refuse_commits(self, said: str) -> None: ...
    def ignore(self, path: str) -> None: ...
    def after_reset_tip_check(
        self, patch: pytest.MonkeyPatch, act: Callable[[], None]
    ) -> None: ...


def task_worktree(world: GitWorld, name: str = "fix-the-login") -> Path:
    """A worktree of a task branch, cut from `main`."""
    path = world.worktrees / name
    world.git.worktree_add(world.checkout, path, name, "main")
    return path


def commit_file(world: GitWorld, where: Path, path: str, body: bytes) -> str:
    """Write and commit one file in a worktree."""
    (where / path).parent.mkdir(parents=True, exist_ok=True)
    (where / path).write_bytes(body)
    made = world.git.commit(where, f"change {path}", (path,))
    assert isinstance(made, str), made
    return made


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
        assert isinstance(made, str), made
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
        assert world.git.push(where, "fix-the-login", None, commit=first) == first
        again = world.git.push(where, "fix-the-login", None, commit=first)
        assert isinstance(again, GitRefused)
        second = commit_file(world, where, "a.txt", b"aa\n")
        assert world.git.push(where, "fix-the-login", first, commit=second) == second
        teammate = world.outside_commit("fix-the-login", {"t.txt": b"t\n"})
        third = commit_file(world, where, "a.txt", b"aaa\n")
        refused = world.git.push(where, "fix-the-login", second, commit=third)
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

    def test_a_rebase_drops_a_merge_commit_and_the_edit_only_it_made(
        self, tmp_path: Path
    ) -> None:
        world = self.world(tmp_path)
        where = task_worktree(world)
        commit_file(world, where, "a.txt", b"a\n")
        world.outside_commit("main", {"other.txt": b"o\n"})
        world.git.fetch(where)
        merge = world.merge_in(where, "origin/main", {"merge-only.txt": b"m\n"})
        assert world.git.show(where, merge, "merge-only.txt") == b"m\n"
        rebased = world.git.rebase(where, "origin/main", reapply=False)
        assert isinstance(rebased, str)
        assert world.git.show(where, rebased, "a.txt") == b"a\n"
        assert world.git.show(where, rebased, "merge-only.txt") is None
        assert [
            c.subject for c in world.git.commits(where, "origin/main", rebased)
        ] == ["change a.txt"]

    def test_an_existing_worktree_path_is_a_fault(self, tmp_path: Path) -> None:
        world = self.world(tmp_path)
        task_worktree(world)
        with pytest.raises(Exception, match="already exists"):
            task_worktree(world)

    def test_a_push_sends_the_commit_named_and_not_a_later_one_of_the_branch(
        self, tmp_path: Path
    ) -> None:
        world = self.world(tmp_path)
        where = task_worktree(world)
        checked = commit_file(world, where, "a.txt", b"a\n")
        later = commit_file(world, where, "b.txt", b"b\n")
        sent = world.git.push(where, "fix-the-login", None, commit=checked)
        assert sent == checked
        world.git.fetch(where)
        assert world.git.remote_head(where, "fix-the-login") == checked
        assert world.git.tip(where, "HEAD") == later

    def test_the_branch_a_checkout_is_on_and_origins_address(
        self, tmp_path: Path
    ) -> None:
        world = self.world(tmp_path)
        where = task_worktree(world)
        assert world.git.branch_of(where) == "fix-the-login"
        assert world.git.branch_of(world.checkout) == "main"
        assert world.git.origin_url(world.checkout)

    def test_an_update_push_sends_the_checked_commit_under_the_existing_lease(
        self, tmp_path: Path
    ) -> None:
        world = self.world(tmp_path)
        branch = "fix-the-login"
        where = task_worktree(world, branch)
        first = commit_file(world, where, "a.txt", b"first\n")
        assert world.git.push(where, branch, None, commit=first) == first
        checked = commit_file(world, where, "a.txt", b"checked\n")
        later = commit_file(world, where, "a.txt", b"later\n")
        assert world.git.push(where, branch, first, commit=checked) == checked
        world.git.fetch(where)
        assert world.git.remote_head(where, branch) == checked
        assert world.git.tip(where, "HEAD") == later

    def test_a_clean_of_tracked_files_only_reads_past_an_untracked_file(
        self, tmp_path: Path
    ) -> None:
        world = self.world(tmp_path)
        where = task_worktree(world)
        (where / "new.txt").write_bytes(b"n\n")
        assert not world.git.clean(where)
        assert world.git.clean(where, untracked=False)
        (where / "README.md").write_bytes(b"changed\n")
        assert not world.git.clean(where, untracked=False)

    def test_the_files_of_a_folder_at_a_commit_and_the_paths_a_range_changed(
        self, tmp_path: Path
    ) -> None:
        world = self.world(tmp_path)
        where = task_worktree(world)
        base = world.git.tip(where, "HEAD")
        assert base is not None
        commit_file(world, where, "docs/backlog/b.md", b"b\n")
        commit_file(world, where, "docs/backlog/a.md", b"a\n")
        tip = commit_file(world, where, "other.txt", b"o\n")
        folder = "docs/backlog"
        assert world.git.files(where, tip, folder) == (
            "docs/backlog/a.md",
            "docs/backlog/b.md",
        )
        assert world.git.files(where, base, folder) == ()
        assert world.git.changed_paths(where, base, tip) == (
            "docs/backlog/a.md",
            "docs/backlog/b.md",
            "other.txt",
        )
        (where / "docs/backlog/a.md").rename(where / "docs/backlog/c.md")
        moved = world.git.commit(
            where, "move a", ("docs/backlog/a.md", "docs/backlog/c.md")
        )
        assert isinstance(moved, str)
        assert world.git.changed_paths(where, tip, moved) == (
            "docs/backlog/a.md",
            "docs/backlog/c.md",
        )

    def test_a_commit_names_its_author_and_a_teammates_names_the_teammate(
        self, tmp_path: Path
    ) -> None:
        world = self.world(tmp_path)
        where = task_worktree(world)
        base = world.git.tip(where, "HEAD")
        assert base is not None
        commit_file(world, where, "a.txt", b"a\n")
        theirs = world.outside_commit("main", {"t.txt": b"t\n"})
        world.git.fetch(where)
        ours = world.git.commits(where, base, "HEAD")
        outside = world.git.commits(where, base, theirs)
        assert [one.author for one in ours] == ["Lem Test"]
        assert [one.author for one in outside] == ["A Teammate"]

    def test_path_facts_name_the_files_that_git_can_read(self, tmp_path: Path) -> None:
        world = self.world(tmp_path)
        where = task_worktree(world)
        base = world.git.tip(where, "HEAD")
        assert base is not None
        path = "docs/backlog/less<than\na.md"
        tip = commit_file(world, where, path, b"the item\n")
        listed = world.git.files(where, tip, "docs/backlog")
        changed = world.git.changed_paths(where, base, tip)
        assert listed == changed == (path,)
        assert world.git.show(where, tip, listed[0]) == b"the item\n"

    def test_the_commits_a_base_holds_already_by_their_patch_are_left_out(
        self, tmp_path: Path
    ) -> None:
        world = self.world(tmp_path)
        where = task_worktree(world)
        same = commit_file(world, where, "a.txt", b"a\n")
        spaced = commit_file(world, where, "sum.py", b"sum = 1\n")
        commit_file(world, where, "b.txt", b"b\n")
        assert world.git.left_out(where, "main", "HEAD") == ()
        world.outside_commit("main", {"a.txt": b"a\n"})
        world.outside_commit("main", {"sum.py": b"sum=1\n"})
        world.outside_commit("main", {"b.txt": b"different\n"})
        world.git.fetch(where)
        found = world.git.left_out(where, "origin/main", "HEAD")
        assert [(one.sha, one.subject) for one in found] == [
            (same, "change a.txt"),
            (spaced, "change sum.py"),
        ]

    def test_a_branch_is_added_with_no_worktree_once(self, tmp_path: Path) -> None:
        world = self.world(tmp_path)
        base = world.git.tip(world.checkout, "main")
        assert world.git.branch_add(world.checkout, "spare", "main") == base
        assert world.git.tip(world.checkout, "spare") == base
        again = world.git.branch_add(world.checkout, "spare", "main")
        assert isinstance(again, GitRefused)

    def test_a_branch_moves_back_only_from_the_commit_named_and_with_nothing_unsaved(
        self, tmp_path: Path
    ) -> None:
        world = self.world(tmp_path)
        where = task_worktree(world)
        before = commit_file(world, where, "a.txt", b"a\n")
        after = commit_file(world, where, "b.txt", b"b\n")
        assert isinstance(world.git.reset(where, before, before), GitRefused)
        (where / "a.txt").write_bytes(b"unsaved\n")
        assert isinstance(world.git.reset(where, before, after), GitRefused)
        (where / "a.txt").write_bytes(b"a\n")
        assert world.git.reset(where, before, after) == before
        assert world.git.tip(where, "HEAD") == before
        assert not (where / "b.txt").exists()
        assert world.git.clean(where)

    def test_a_commit_a_hook_refuses_is_gits_refusal_in_its_words(
        self, tmp_path: Path
    ) -> None:
        world = self.world(tmp_path)
        where = task_worktree(world)
        before = world.git.tip(where, "HEAD")
        world.refuse_commits("the hook says no")
        (where / "a.txt").write_bytes(b"a\n")
        refused = world.git.commit(where, "add a", ("a.txt",))
        assert isinstance(refused, GitRefused)
        assert "the hook says no" in refused.said
        assert world.git.tip(where, "HEAD") == before

    def test_a_reset_preserves_a_commit_made_after_its_tip_check(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        world = self.world(tmp_path)
        where = task_worktree(world)
        before = commit_file(world, where, "a.txt", b"a\n")
        expected = commit_file(world, where, "b.txt", b"b\n")
        committed: list[str] = []

        def commit_during_reset() -> None:
            committed.append(commit_file(world, where, "c.txt", b"new work\n"))

        with monkeypatch.context() as patch:
            world.after_reset_tip_check(patch, commit_during_reset)
            refused = world.git.reset(where, before, expected)

        assert len(committed) == 1
        assert world.git.tip(where, "HEAD") == committed[0]
        assert (where / "b.txt").read_bytes() == b"b\n"
        assert (where / "c.txt").read_bytes() == b"new work\n"
        assert world.git.clean(where)
        assert isinstance(refused, GitRefused)

    def test_reset_refuses_to_replace_an_untracked_file(self, tmp_path: Path) -> None:
        world = self.world(tmp_path)
        where = task_worktree(world)
        before = world.git.tip(where, "HEAD")
        assert before is not None
        path = where / "README.md"
        path.unlink()
        removed = world.git.commit(where, "remove the readme", (path.name,))
        assert isinstance(removed, str), removed
        path.write_bytes(b"unsaved\n")
        assert world.git.clean(where, untracked=False)
        assert isinstance(world.git.reset(where, before, removed), GitRefused)
        assert path.read_bytes() == b"unsaved\n"
        assert world.git.tip(where, "HEAD") == removed

    @pytest.mark.parametrize(
        ("tracked", "local"),
        [
            pytest.param("env", "env", id="file"),
            pytest.param("env", "env/local", id="local-folder"),
            pytest.param("env/tracked", "env", id="target-folder"),
        ],
    )
    def test_reset_refuses_to_replace_ignored_data(
        self, tmp_path: Path, tracked: str, local: str
    ) -> None:
        world = self.world(tmp_path)
        where = task_worktree(world)
        target = commit_file(world, where, tracked, b"tracked\n")
        (where / tracked).unlink()
        current = world.git.commit(where, "remove the tracked file", (tracked,))
        assert isinstance(current, str), current
        world.ignore("env")
        path = where / local
        if path.is_dir():
            path.rmdir()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"local only\n")
        assert world.git.clean(where)
        assert isinstance(world.git.reset(where, target, current), GitRefused)
        assert path.read_bytes() == b"local only\n"
        assert world.git.tip(where, "HEAD") == current

    def test_reset_keeps_ignored_data_beside_a_restored_file(
        self, tmp_path: Path
    ) -> None:
        world = self.world(tmp_path)
        where = task_worktree(world)
        target = commit_file(world, where, "env/tracked", b"tracked\n")
        (where / "env/tracked").unlink()
        current = world.git.commit(where, "remove the tracked file", ("env/tracked",))
        assert isinstance(current, str), current
        world.ignore("env")
        path = where / "env/local"
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(b"local only\n")
        assert world.git.clean(where)
        assert world.git.reset(where, target, current) == target
        assert path.read_bytes() == b"local only\n"
        assert (where / "env/tracked").read_bytes() == b"tracked\n"

    def test_a_merge_makes_a_merge_commit_of_the_branch_and_the_ref(
        self, tmp_path: Path
    ) -> None:
        world = self.world(tmp_path)
        where = task_worktree(world)
        tip = commit_file(world, where, "a.txt", b"a\n")
        pushed = world.outside_commit("main", {"other.txt": b"o\n"})
        world.git.fetch(where)
        message = "Merge origin/main into fix-the-login"
        made = world.git.merge(where, pushed, message)
        assert isinstance(made, str), made
        assert world.git.tip(where, "HEAD") == made
        last = world.git.commits(where, tip, made)[-1]
        assert (last.sha, last.parents, last.subject) == (made, (tip, pushed), message)
        assert world.git.show(where, made, "a.txt") == b"a\n"
        assert (where / "other.txt").read_bytes() == b"o\n"
        assert world.git.clean(where)
        assert not world.git.remerge(where, made).strip()
        assert world.git.merge(where, pushed, message) == made

    def test_a_conflicting_merge_waits_for_a_builder_and_its_resolution_is_the_remerge(
        self, tmp_path: Path
    ) -> None:
        world = self.world(tmp_path)
        where = task_worktree(world)
        tip = commit_file(world, where, "README.md", b"ours\n")
        theirs = world.outside_commit("main", {"README.md": b"theirs\n"})
        world.git.fetch(where)
        stopped = world.git.merge(where, theirs, "Merge origin/main")
        assert stopped == Conflict(files=("README.md",))
        assert world.git.tip(where, "HEAD") == tip
        assert not world.git.clean(where)
        partial = world.git.commit(where, "a partial commit", ("README.md",))
        assert isinstance(partial, GitRefused)
        resolved = world.resolve(where, {"README.md": b"resolved\n"})
        assert world.git.commits(where, tip, resolved)[-1].parents == (tip, theirs)
        shown = world.git.remerge(where, resolved)
        assert "README.md" in shown
        assert "+resolved" in shown

    def test_a_merge_git_refuses_leaves_the_worktree_as_it_was(
        self, tmp_path: Path
    ) -> None:
        world = self.world(tmp_path)
        where = task_worktree(world)
        tip = commit_file(world, where, "a.txt", b"a\n")
        theirs = world.outside_commit("main", {"README.md": b"theirs\n"})
        world.git.fetch(where)
        (where / "README.md").write_bytes(b"unsaved\n")
        refused = world.git.merge(where, theirs, "Merge origin/main")
        assert isinstance(refused, GitRefused)
        assert world.git.tip(where, "HEAD") == tip
        assert (where / "README.md").read_bytes() == b"unsaved\n"
        (where / "README.md").write_bytes(FILES["README.md"])
        assert world.git.clean(where)
        assert isinstance(world.git.merge(where, theirs, "Merge origin/main"), str)
