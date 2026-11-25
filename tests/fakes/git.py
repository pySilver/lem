"""`ModelGit`: the `Git` port over a repository held in memory, for the model level and the
contract suite (`tests/contract/suites/git.py`).

The commits, the branches, the remote's branches and the ones last fetched live in memory; a
worktree's files live on disk, so a test writes a file and commits it through the port as it
would with real git. A tree is a mapping of path to bytes, and its id and a commit's sha are
sha1 digests, 40 hex characters. A merge and a rebase are three-way, path by path: a path both
sides changed to different bytes is a conflict.

`outside_commit` and `outside_merge` stand for what someone else does on the remote: a
teammate's push, a merge on GitHub. `Remote` is what `LocalForge` merges through.
"""

import hashlib
import shutil
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from lem.ports.faults import Unanswered
from lem.ports.git_facts import Commit, Conflict, DiffStat, GitRefused, RebaseState

if TYPE_CHECKING:
    from pathlib import Path

type Tree = dict[str, bytes]


def tree_id(tree: Tree) -> str:
    """The id of a tree: the digest of its sorted paths and their bytes' digests."""
    lines = "".join(
        f"{path}\0{hashlib.sha1(tree[path], usedforsecurity=False).hexdigest()}\n"
        for path in sorted(tree)
    )
    return hashlib.sha1(f"tree\n{lines}".encode(), usedforsecurity=False).hexdigest()


@dataclass(frozen=True)
class Stored:
    """A commit in the model: its tree, parents and message."""

    tree: Tree
    parents: tuple[str, ...]
    message: str


@dataclass
class Worktree:
    """A worktree: its branch, and a rebase that stopped in it."""

    branch: str
    rebase: RebaseState | None = None
    before_rebase: str | None = None


def merged(base: Tree, ours: Tree, theirs: Tree) -> Tree | Conflict:
    """The three-way merge of two trees over their base, path by path."""
    result: Tree = {}
    clashes: list[str] = []
    for path in sorted(base.keys() | ours.keys() | theirs.keys()):
        was, mine, other = base.get(path), ours.get(path), theirs.get(path)
        if other in {mine, was}:
            kept = mine
        elif mine == was:
            kept = other
        else:
            clashes.append(path)
            continue
        if kept is not None:
            result[path] = kept
    return Conflict(files=tuple(clashes)) if clashes else result


@dataclass
class ModelGit:
    """A repository, its remote and its worktrees, in memory but the worktrees' files."""

    checkout: Path
    objects: dict[str, Stored] = field(default_factory=dict)
    branches: dict[str, str] = field(default_factory=dict)
    remote: dict[str, str] = field(default_factory=dict)
    fetched: dict[str, str] = field(default_factory=dict)
    worktrees: dict[Path, Worktree] = field(default_factory=dict)
    count: int = 0

    # ---- making a world ----

    @classmethod
    def init(cls, checkout: Path, files: Tree, branch: str = "main") -> ModelGit:
        """A repository at `checkout` with one commit of `files` on `branch`, pushed and
        fetched."""
        model = cls(checkout=checkout)
        first = model.store(dict(files), (), "the first commit")
        model.branches[branch] = model.remote[branch] = model.fetched[branch] = first
        model.worktrees[checkout] = Worktree(branch=branch)
        model.lay(checkout, dict(files))
        return model

    def store(self, tree: Tree, parents: tuple[str, ...], message: str) -> str:
        """Keep a commit and give its sha."""
        self.count += 1
        body = f"{tree_id(tree)}\n{' '.join(parents)}\n{message}\n{self.count}"
        sha = hashlib.sha1(body.encode(), usedforsecurity=False).hexdigest()
        self.objects[sha] = Stored(tree=tree, parents=parents, message=message)
        return sha

    def outside_commit(
        self, branch: str, files: dict[str, bytes | None], start: str = "main"
    ) -> str:
        """A commit someone else pushed to the remote's `branch`, made from the remote's
        `start` when the branch is new: `files` over its tree, None for a removed file."""
        parent = self.remote.get(branch) or self.remote[start]
        tree = dict(self.objects[parent].tree)
        for path, body in files.items():
            if body is None:
                tree.pop(path, None)
            else:
                tree[path] = body
        self.remote[branch] = self.store(
            tree, (parent,), f"outside: {', '.join(files)}"
        )
        return self.remote[branch]

    def lay(self, where: Path, tree: Tree) -> None:
        """Make the files of `where` the files of `tree`."""
        for path in self.on_disk(where):
            if path not in tree:
                (where / path).unlink()
        for path, body in tree.items():
            target = where / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(body)

    def on_disk(self, where: Path) -> Tree:
        """The files of a worktree as they are on disk."""
        if not where.is_dir():
            return {}
        return {
            str(path.relative_to(where)): path.read_bytes()
            for path in where.rglob("*")
            if path.is_file()
        }

    def worktree(self, where: Path) -> Worktree:
        """The worktree at `where`, or the fault a real git would give."""
        found = self.worktrees.get(where)
        if found is None:
            raise Unanswered("git", f"{where} is no worktree of {self.checkout}")
        return found

    def resolve(self, where: Path, rev: str) -> str | None:
        """A ref, `HEAD`, `origin/BRANCH` or a sha, as a sha."""
        if rev == "HEAD":
            return self.branches.get(self.worktree(where).branch)
        if rev.startswith("origin/"):
            return self.fetched.get(rev.removeprefix("origin/"))
        if rev in self.branches:
            return self.branches[rev]
        return rev if rev in self.objects else None

    def must(self, where: Path, rev: str) -> str:
        """`resolve`, or the fault for a rev git does not know."""
        sha = self.resolve(where, rev)
        if sha is None:
            raise Unanswered("git", f"unknown revision {rev}")
        return sha

    def ancestors(self, sha: str) -> set[str]:
        """`sha` and every commit it descends from."""
        seen: set[str] = set()
        todo = [sha]
        while todo:
            current = todo.pop()
            if current not in seen:
                seen.add(current)
                todo.extend(self.objects[current].parents)
        return seen

    # ---- GitHistory ----

    def tip(self, where: Path, ref: str) -> str | None:
        return self.resolve(where, ref)

    def tree(self, where: Path, rev: str) -> str:
        return tree_id(self.objects[self.must(where, rev)].tree)

    def merge_base(self, where: Path, first: str, second: str) -> str | None:
        common = self.ancestors(self.must(where, first)) & self.ancestors(
            self.must(where, second)
        )
        best = [
            sha
            for sha in common
            if not any(sha in self.ancestors(other) - {other} for other in common)
        ]
        return best[0] if best else None

    def is_ancestor(self, where: Path, older: str, newer: str) -> bool:
        return self.must(where, older) in self.ancestors(self.must(where, newer))

    def commits_of(self, since: str, until: str) -> list[str]:
        """The commits of `until` that `since` lacks, oldest first, first parents only."""
        known = self.ancestors(since)
        line: list[str] = []
        current: str | None = until
        while current is not None and current not in known:
            line.append(current)
            parents = self.objects[current].parents
            current = parents[0] if parents else None
        return line[::-1]

    def commits(self, where: Path, since: str, until: str) -> tuple[Commit, ...]:
        found = self.commits_of(self.must(where, since), self.must(where, until))
        return tuple(
            Commit(
                sha=sha,
                parents=self.objects[sha].parents,
                subject=self.objects[sha].message.splitlines()[0],
            )
            for sha in found
        )

    def diff_stat(self, where: Path, since: str, until: str) -> DiffStat:
        before = self.objects[self.must(where, since)].tree
        after = self.objects[self.must(where, until)].tree
        paths = tuple(
            sorted(
                p for p in before.keys() | after.keys() if before.get(p) != after.get(p)
            )
        )
        added = sum(len(after.get(p, b"").splitlines()) for p in paths)
        removed = sum(len(before.get(p, b"").splitlines()) for p in paths)
        return DiffStat(paths=paths, added=added, removed=removed)

    def merge_tree(self, where: Path, base: str, tip: str) -> str | Conflict:
        ours, theirs = self.must(where, base), self.must(where, tip)
        common = self.merge_base(where, ours, theirs)
        start = self.objects[common].tree if common else {}
        result = merged(start, self.objects[ours].tree, self.objects[theirs].tree)
        return result if isinstance(result, Conflict) else tree_id(result)

    # ---- GitPlaces ----

    def main_checkout(self, start: Path) -> Path:
        if start != self.checkout and start not in self.worktrees:
            raise Unanswered("git", f"{start} is not in a repository")
        return self.checkout

    def clean(self, where: Path) -> bool:
        head = self.resolve(where, "HEAD")
        return head is not None and self.on_disk(where) == self.objects[head].tree

    def show(self, where: Path, rev: str, path: str) -> bytes | None:
        return self.objects[self.must(where, rev)].tree.get(path)

    def rebase_state(self, where: Path) -> RebaseState | None:
        return self.worktree(where).rebase

    def remote_head(self, where: Path, branch: str) -> str | None:
        return self.fetched.get(branch)

    # ---- GitRewrite ----

    def fetch(self, where: Path) -> None:
        self.fetched = dict(self.remote)

    def rebase(
        self, worktree: Path, onto: str, *, reapply: bool
    ) -> str | Conflict | GitRefused:
        place = self.worktree(worktree)
        if place.rebase is not None:
            return GitRefused(said="a rebase is in progress")
        if not self.clean(worktree):
            return GitRefused(said="cannot rebase: you have unstaged changes")
        head, target = self.must(worktree, "HEAD"), self.must(worktree, onto)
        current = target
        for sha in self.commits_of(target, head):
            stored = self.objects[sha]
            parent = self.objects[stored.parents[0]].tree if stored.parents else {}
            applied = merged(parent, self.objects[current].tree, stored.tree)
            if isinstance(applied, Conflict):
                place.rebase = RebaseState(onto=target, files=applied.files)
                place.before_rebase = head
                return applied
            if applied == self.objects[current].tree and not reapply:
                continue
            current = self.store(applied, (current,), stored.message)
        self.branches[place.branch] = current
        self.lay(worktree, self.objects[current].tree)
        return current

    def abort(self, worktree: Path) -> None:
        place = self.worktree(worktree)
        place.rebase = None
        place.before_rebase = None
        self.lay(worktree, self.objects[self.must(worktree, "HEAD")].tree)

    def commit(self, worktree: Path, message: str, paths: tuple[str, ...]) -> str:
        place = self.worktree(worktree)
        head = self.must(worktree, "HEAD")
        tree = dict(self.objects[head].tree)
        disk = self.on_disk(worktree)
        for path in paths:
            if path in disk:
                tree[path] = disk[path]
            else:
                tree.pop(path, None)
        self.branches[place.branch] = self.store(tree, (head,), message)
        return self.branches[place.branch]

    def push(self, worktree: Path, branch: str, expect: str | None) -> str | GitRefused:
        there = self.remote.get(branch)
        if there != expect:
            return GitRefused(said=f"stale info: {branch} is at {there}, not {expect}")
        self.remote[branch] = self.fetched[branch] = self.branches[branch]
        return self.branches[branch]

    # ---- GitBranches ----

    def worktree_add(self, checkout: Path, path: Path, branch: str, start: str) -> None:
        if path in self.worktrees or path.exists():
            raise Unanswered("git", f"{path} already exists")
        if branch not in self.branches:
            self.branches[branch] = self.must(checkout, start)
        self.worktrees[path] = Worktree(branch=branch)
        self.lay(path, self.objects[self.branches[branch]].tree)

    def worktree_remove(self, checkout: Path, path: Path) -> None:
        self.worktree(path)
        del self.worktrees[path]
        shutil.rmtree(path)

    def branch_delete(self, checkout: Path, branch: str, expect: str) -> bool:
        if self.branches.get(branch) != expect:
            return False
        if any(place.branch == branch for place in self.worktrees.values()):
            return False
        del self.branches[branch]
        return True

    def fast_forward(self, checkout: Path, ref: str) -> str | GitRefused:
        head, target = self.must(checkout, "HEAD"), self.must(checkout, ref)
        if head not in self.ancestors(target):
            return GitRefused(said="fatal: Not possible to fast-forward, aborting.")
        self.branches[self.worktree(checkout).branch] = target
        self.lay(checkout, self.objects[target].tree)
        return target

    # ---- Remote, for LocalForge ----

    def head_of(self, branch: str) -> str | None:
        """The remote's `branch`."""
        return self.remote.get(branch)

    def merge_into(
        self, base: str, head: str, *, squash: bool, message: str
    ) -> str | Conflict:
        """Merge the commit `head` into the remote's `base`, as the forge does."""
        target = self.remote[base]
        common = self.merge_base(self.checkout, target, head)
        start = self.objects[common].tree if common else {}
        result = merged(start, self.objects[target].tree, self.objects[head].tree)
        if isinstance(result, Conflict):
            return result
        parents = (target,) if squash else (target, head)
        self.remote[base] = self.store(result, parents, message)
        return self.remote[base]

    def delete_remote(self, branch: str, expect: str) -> bool:
        """Delete the remote's `branch` only at `expect`."""
        if self.remote.get(branch) != expect:
            return False
        del self.remote[branch]
        return True
