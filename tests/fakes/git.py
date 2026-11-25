"""`ModelGit`: the `Git` port over a repository held in memory, for the model level and the
contract suite (`tests/contract/suites/git.py`).

The commits, the branches, the remote's branches and the ones last fetched live in memory; a
worktree's files live on disk, so a test writes a file and commits it through the port as it
would with real git. A tree is a mapping of path to bytes, and its id and a commit's sha are
sha1 digests, 40 hex characters. A merge and a rebase are three-way, path by path: a path both
sides changed to different bytes is a conflict.

`outside_commit` and `outside_merge` stand for what someone else does on the remote: a
teammate's push, under the teammate's name, a merge on GitHub. `Remote` is what `LocalForge`
merges through. `refused_commit` stands for a commit hook that refuses every commit.
"""

import hashlib
import shutil
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from lem.ports.faults import Unanswered
from lem.ports.git_facts import Commit, Conflict, DiffStat, GitRefused, RebaseState

if TYPE_CHECKING:
    from collections.abc import Collection
    from pathlib import Path

    from lem.ports.forge_facts import MergeMethod

type Tree = dict[str, bytes]

# The author of the commits a test makes, and of a teammate's, as `tests/fakes/repo.py` names them.
OWN = "Lem Test"
TEAMMATE = "A Teammate"


def tree_id(tree: Tree) -> str:
    """The id of a tree: the digest of its sorted paths and their bytes' digests."""
    lines = "".join(
        f"{path}\0{hashlib.sha1(tree[path], usedforsecurity=False).hexdigest()}\n"
        for path in sorted(tree)
    )
    return hashlib.sha1(f"tree\n{lines}".encode(), usedforsecurity=False).hexdigest()


@dataclass(frozen=True)
class Landed:
    """A merge the remote made: its commit, and the commit of the base it went onto."""

    commit: str
    base_parent: str


@dataclass(frozen=True)
class Stored:
    """A commit in the model: its tree, parents, message and author."""

    tree: Tree
    parents: tuple[str, ...]
    message: str
    author: str = OWN


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
    origin: str | None = "git@github.com:acme/shop.git"
    refused_commit: str | None = None
    ignored: set[str] = field(default_factory=set)

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

    def store(
        self, tree: Tree, parents: tuple[str, ...], message: str, author: str = OWN
    ) -> str:
        """Keep a commit and give its sha."""
        self.count += 1
        body = f"{tree_id(tree)}\n{' '.join(parents)}\n{message}\n{self.count}"
        sha = hashlib.sha1(body.encode(), usedforsecurity=False).hexdigest()
        self.objects[sha] = Stored(
            tree=tree, parents=parents, message=message, author=author
        )
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
            tree, (parent,), f"outside: {', '.join(files)}", TEAMMATE
        )
        return self.remote[branch]

    def outside_merge_commit(
        self, branch: str, other: str, files: dict[str, bytes]
    ) -> str:
        """A merge commit of the remote's `other` into its `branch` that someone else pushed,
        with `files` edited in the merge itself."""
        head, theirs = self.remote[branch], self.remote[other]
        common = self.merge_base(self.checkout, head, theirs)
        start = self.objects[common].tree if common else {}
        result = merged(start, self.objects[head].tree, self.objects[theirs].tree)
        if isinstance(result, Conflict):
            raise Unanswered("git", f"the merge of {other} conflicts on {result.files}")
        self.remote[branch] = self.store(
            {**result, **files}, (head, theirs), f"Merge {other}", TEAMMATE
        )
        return self.remote[branch]

    def lay(self, where: Path, tree: Tree, *, keep: Collection[str] = ()) -> None:
        """Make the files of `where` the files of `tree`, with local files in `keep`."""
        for path in self.on_disk(where):
            if path not in tree and path not in keep:
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
        """The commits of `until` that `since` lacks, oldest first (`git rev-list --reverse`):
        a commit is stored after its parents, so the order of storing is an order of history."""
        wanted = self.ancestors(until) - self.ancestors(since)
        return [sha for sha in self.objects if sha in wanted]

    def replayed(
        self, onto: str, head: str, *, reapply: bool
    ) -> tuple[str, Conflict | None]:
        """Replay the commits of `head` that `onto` lacks onto `onto`, as `git rebase` does:
        a merge commit is dropped, with any edit only it made, and a commit whose change `onto`
        holds already is dropped too unless `reapply`. The new tip, or where it stopped and
        the conflict."""
        current = onto
        for sha in self.commits_of(onto, head):
            stored = self.objects[sha]
            if len(stored.parents) > 1:
                continue
            parent = self.objects[stored.parents[0]].tree if stored.parents else {}
            applied = merged(parent, self.objects[current].tree, stored.tree)
            if isinstance(applied, Conflict):
                return current, applied
            if applied == self.objects[current].tree and not reapply:
                continue
            current = self.store(applied, (current,), stored.message, stored.author)
        return current, None

    def merge_in(self, where: Path, ref: str, files: dict[str, bytes]) -> str:
        """A merge commit of `ref` into the worktree's branch, made by hand, with `files`
        edited in the merge itself: the change a plain rebase drops."""
        place = self.worktree(where)
        head, other = self.must(where, "HEAD"), self.must(where, ref)
        common = self.merge_base(where, head, other)
        start = self.objects[common].tree if common else {}
        result = merged(start, self.objects[head].tree, self.objects[other].tree)
        if isinstance(result, Conflict):
            raise Unanswered("git", f"the merge of {ref} conflicts on {result.files}")
        made = self.store({**result, **files}, (head, other), f"Merge {ref}")
        self.branches[place.branch] = made
        self.lay(where, self.objects[made].tree)
        return made

    def commits(self, where: Path, since: str, until: str) -> tuple[Commit, ...]:
        found = self.commits_of(self.must(where, since), self.must(where, until))
        return tuple(self.commit_of(sha) for sha in found)

    def commit_of(self, sha: str) -> Commit:
        """The commit `sha` as the port gives it."""
        stored = self.objects[sha]
        return Commit(
            sha=sha,
            parents=stored.parents,
            subject=stored.message.splitlines()[0],
            author=stored.author,
        )

    def patch_of(self, sha: str) -> dict[str, tuple[bytes | None, bytes | None]]:
        """What the commit `sha` changed over its first parent, path by path."""
        stored = self.objects[sha]
        parent = self.objects[stored.parents[0]].tree if stored.parents else {}
        return {
            path: (parent.get(path), stored.tree.get(path))
            for path in parent.keys() | stored.tree.keys()
            if parent.get(path) != stored.tree.get(path)
        }

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

    # ---- GitChanges ----

    def files(self, where: Path, rev: str, folder: str) -> tuple[str, ...]:
        tree = self.objects[self.must(where, rev)].tree
        inside = f"{folder.strip('/')}/"
        return tuple(sorted(path for path in tree if path.startswith(inside)))

    def changed_paths(self, where: Path, since: str, until: str) -> tuple[str, ...]:
        return self.diff_stat(where, since, until).paths

    def left_out(self, where: Path, onto: str, tip: str) -> tuple[Commit, ...]:
        base, head = self.must(where, onto), self.must(where, tip)
        theirs = [
            self.patch_of(sha)
            for sha in self.commits_of(head, base)
            if len(self.objects[sha].parents) == 1
        ]
        return tuple(
            self.commit_of(sha)
            for sha in self.commits_of(base, head)
            if len(self.objects[sha].parents) == 1 and self.patch_of(sha) in theirs
        )

    # ---- GitPlaces ----

    def main_checkout(self, start: Path) -> Path:
        if start != self.checkout and start not in self.worktrees:
            raise Unanswered("git", f"{start} is not in a repository")
        return self.checkout

    def branch_of(self, where: Path) -> str | None:
        return self.worktree(where).branch

    def clean(self, where: Path, *, untracked: bool = True) -> bool:
        head = self.resolve(where, "HEAD")
        if head is None:
            return False
        tree, disk = self.objects[head].tree, self.on_disk(where)
        if any(disk.get(path) != body for path, body in tree.items()):
            return False
        extra = disk.keys() - tree.keys()
        return not untracked or extra == self.ignored_paths(extra)

    def ignored_paths(self, paths: set[str]) -> set[str]:
        """The paths under the model's literal exclude entries."""
        return {
            path
            for path in paths
            if any(path == name or path.startswith(f"{name}/") for name in self.ignored)
        }

    def show(self, where: Path, rev: str, path: str) -> bytes | None:
        return self.objects[self.must(where, rev)].tree.get(path)

    def rebase_state(self, where: Path) -> RebaseState | None:
        return self.worktree(where).rebase

    def remote_head(self, where: Path, branch: str) -> str | None:
        return self.fetched.get(branch)

    def origin_url(self, where: Path) -> str | None:
        return self.origin

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
        current, stopped = self.replayed(target, head, reapply=reapply)
        if stopped is not None:
            place.rebase = RebaseState(onto=target, files=stopped.files)
            place.before_rebase = head
            return stopped
        self.branches[place.branch] = current
        self.lay(worktree, self.objects[current].tree)
        return current

    def abort(self, worktree: Path) -> None:
        place = self.worktree(worktree)
        place.rebase = None
        place.before_rebase = None
        self.lay(worktree, self.objects[self.must(worktree, "HEAD")].tree)

    def commit(
        self, worktree: Path, message: str, paths: tuple[str, ...]
    ) -> str | GitRefused:
        if self.refused_commit is not None:
            return GitRefused(said=self.refused_commit)
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

    def push(
        self, worktree: Path, branch: str, expect: str | None, *, commit: str
    ) -> str | GitRefused:
        there = self.remote.get(branch)
        if there != expect:
            return GitRefused(said=f"stale info: {branch} is at {there}, not {expect}")
        self.remote[branch] = self.fetched[branch] = self.must(worktree, commit)
        return self.remote[branch]

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

    def branch_add(self, checkout: Path, branch: str, start: str) -> str | GitRefused:
        if branch in self.branches:
            return GitRefused(said=f"fatal: a branch named '{branch}' already exists")
        self.branches[branch] = self.must(checkout, start)
        return self.branches[branch]

    def reset(self, worktree: Path, commit: str, expect: str) -> str | GitRefused:
        place = self.worktree(worktree)
        if self.branches.get(place.branch) != expect:
            return GitRefused(said=f"the branch is not at {expect}")
        if not self.clean(worktree):
            return GitRefused(said="the worktree has changes that no commit holds")
        target = self.must(worktree, commit)
        tree = self.objects[target].tree
        local = self.on_disk(worktree).keys() - self.objects[expect].tree.keys()
        if any(
            path == tracked
            or path.startswith(f"{tracked}/")
            or tracked.startswith(f"{path}/")
            for path in local
            for tracked in tree
        ):
            return GitRefused(said="the reset would overwrite an untracked file")
        self.lay(worktree, tree, keep=local)
        self.branches[place.branch] = target
        return target

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
        self, base: str, head: str, *, method: MergeMethod, message: str
    ) -> Landed | Conflict:
        """Merge the commit `head` into the remote's `base`, as the forge does: one squashed
        commit, a merge commit, or each commit replayed."""
        target = self.remote[base]
        if method == "rebase":
            made, stopped = self.replayed(target, head, reapply=False)
            if stopped is not None:
                return stopped
            self.remote[base] = made
            return Landed(commit=made, base_parent=target)
        common = self.merge_base(self.checkout, target, head)
        start = self.objects[common].tree if common else {}
        result = merged(start, self.objects[target].tree, self.objects[head].tree)
        if isinstance(result, Conflict):
            return result
        parents = (target,) if method == "squash" else (target, head)
        self.remote[base] = self.store(result, parents, message)
        return Landed(commit=self.remote[base], base_parent=target)

    def delete_remote(self, branch: str, expect: str) -> bool:
        """Delete the remote's `branch` only at `expect`."""
        if self.remote.get(branch) != expect:
            return False
        del self.remote[branch]
        return True
