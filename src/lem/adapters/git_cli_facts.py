"""The facts of the `Git` port through real git: the history (`GitHistory`) and the checkouts
(`GitPlaces`); the paths (`GitChanges`) are `git_cli_changes.py`. None of them changes the
repository."""

from pathlib import Path

from lem.adapters.git_cli_names import listed
from lem.adapters.git_cli_shell import GIT, Shell, last_words
from lem.adapters.git_cli_stops import ABSOLUTE, conflicted, rebase_folder, too_old
from lem.ports.faults import Unanswered
from lem.ports.git_facts import Commit, Conflict, DiffStat, RebaseState

# A field of `git log`'s line: the sha, the parents, the author's name, the subject, between
# tabs.
LOG = "--format=%H%x09%P%x09%an%x09%s"
# git's three-way merge with no write to a worktree, an index or a ref, the base as its first
# side as a rebase applies them, and the files of a conflict by the names git wrote.
MERGE_TREE = ("--write-tree", "--name-only", "-z", "--no-messages")


class History(Shell):
    """A ref's tip, a commit's tree, their ancestry, a range and its size, and the tree a
    merge would make."""

    def tip(self, where: Path, ref: str) -> str | None:
        return self.commit_at(where, ref)

    def tree(self, where: Path, rev: str) -> str:
        return self.said(where, "rev-parse", f"{rev}^{{tree}}")

    def merge_base(self, where: Path, first: str, second: str) -> str | None:
        ran = self.tried(where, "merge-base", first, second)
        if ran.returncode > 1:
            raise Unanswered(GIT, last_words(ran))
        return None if ran.returncode else ran.stdout.strip()

    def is_ancestor(self, where: Path, older: str, newer: str) -> bool:
        ran = self.tried(where, "merge-base", "--is-ancestor", older, newer)
        return not ran.returncode

    def commits(self, where: Path, since: str, until: str) -> tuple[Commit, ...]:
        listed = self.said(where, "log", "--reverse", LOG, f"{since}..{until}")
        return tuple(commit_of(line) for line in listed.splitlines() if line)

    def diff_stat(self, where: Path, since: str, until: str) -> DiffStat:
        listed = self.said(where, "diff", "--numstat", since, until)
        rows = [line.split("\t", 2) for line in listed.splitlines() if line]
        return DiffStat(
            paths=tuple(row[2] for row in rows),
            added=sum(counted(row[0]) for row in rows),
            removed=sum(counted(row[1]) for row in rows),
        )

    def merge_tree(self, where: Path, base: str, tip: str) -> str | Conflict:
        ran = self.raw(where, "merge-tree", *MERGE_TREE, base, tip)
        tree, _, named = ran.stdout.partition(b"\0")
        if ran.returncode > 1 or not tree:
            raise Unanswered(GIT, too_old(self, where, ran.stderr))
        if ran.returncode:
            return Conflict(files=tuple(sorted(listed(named))))
        return tree.decode()


class Places(Shell):
    """The main checkout, the branch a checkout is on, a worktree's cleanness and rebase, a file
    at a commit, the remote's branch as last fetched, and origin's address."""

    def main_checkout(self, start: Path) -> Path:
        common = self.said(start, "rev-parse", ABSOLUTE, "--git-common-dir")
        return Path(common).parent

    def branch_of(self, where: Path) -> str | None:
        return self.said(where, "branch", "--show-current") or None

    def clean(self, where: Path, *, untracked: bool = True) -> bool:
        files = "--untracked-files=normal" if untracked else "--untracked-files=no"
        return not self.said(where, "status", "--porcelain", files)

    def show(self, where: Path, rev: str, path: str) -> bytes | None:
        spec = f"{rev}:{path}"
        if self.tried(where, "cat-file", "-e", spec).returncode:
            return None
        return self.blob(where, spec)

    def rebase_state(self, where: Path) -> RebaseState | None:
        folder = rebase_folder(self, where)
        if folder is None:
            return None
        onto = (folder / "onto").read_text(encoding="utf-8").strip()
        return RebaseState(onto=onto, files=conflicted(self, where))

    def remote_head(self, where: Path, branch: str) -> str | None:
        return self.commit_at(where, f"refs/remotes/origin/{branch}")

    def origin_url(self, where: Path) -> str | None:
        # the checkout's own configuration only, as `lem init` reads it (notes/settings.md)
        named = ("config", "--local", "--get", "remote.origin.url")
        return self.tried(where, *named).stdout.strip() or None


def commit_of(line: str) -> Commit:
    """One line of `LOG` as a commit."""
    sha, parents, author, subject = line.split("\t", 3)
    return Commit(
        sha=sha, parents=tuple(parents.split()), author=author, subject=subject
    )


def counted(number: str) -> int:
    """A count of `--numstat`; a binary file's `-` counts no line."""
    return int(number) if number.isdigit() else 0
