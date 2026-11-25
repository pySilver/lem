"""The facts of the `Git` port through real git: the history (`GitHistory`) and the checkouts
(`GitPlaces`). None of them changes the repository."""

from pathlib import Path

from lem.adapters.git_cli_shell import GIT, Shell, last_words
from lem.ports.faults import Unanswered
from lem.ports.git_facts import Commit, Conflict, DiffStat, RebaseState

# A field of `git log`'s line: the sha, the parents, the subject, between tabs.
LOG = "--format=%H%x09%P%x09%s"
REBASE_FOLDERS = ("rebase-merge", "rebase-apply")
ABSOLUTE = "--path-format=absolute"


class History(Shell):
    """A ref's tip, a commit's tree, their ancestry, a range and its size, and the tree a
    merge would make."""

    def tip(self, where: Path, ref: str) -> str | None:
        return self.commit_at(where, ref)

    def tree(self, where: Path, rev: str) -> str:
        return self.said(where, "rev-parse", f"{rev}^{{tree}}")

    def merge_base(self, where: Path, first: str, second: str) -> str | None:
        ran = self.tried(where, "merge-base", first, second)
        return ran.stdout.strip() or None

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
        ran = self.tried(where, "merge-tree", "--write-tree", "--name-only", base, tip)
        lines = ran.stdout.splitlines()
        if ran.returncode > 1 or not lines:
            raise Unanswered(GIT, last_words(ran))
        if ran.returncode:
            return Conflict(files=tuple(conflicted(lines)))
        return lines[0]


class Places(Shell):
    """The main checkout, a worktree's cleanness and rebase, a file at a commit, and the
    remote's branch as last fetched."""

    def main_checkout(self, start: Path) -> Path:
        common = self.said(start, "rev-parse", ABSOLUTE, "--git-common-dir")
        return Path(common).parent

    def clean(self, where: Path) -> bool:
        listed = self.said(where, "status", "--porcelain", "--untracked-files=normal")
        return not listed

    def show(self, where: Path, rev: str, path: str) -> bytes | None:
        spec = f"{rev}:{path}"
        if self.tried(where, "cat-file", "-e", spec).returncode:
            return None
        return self.blob(where, spec)

    def rebase_state(self, where: Path) -> RebaseState | None:
        folders = (self.git_path(where, name) for name in REBASE_FOLDERS)
        folder = next((found for found in folders if found.is_dir()), None)
        if folder is None:
            return None
        onto = (folder / "onto").read_text(encoding="utf-8").strip()
        stopped = self.said(where, "diff", "--name-only", "--diff-filter=U")
        return RebaseState(onto=onto, files=tuple(stopped.splitlines()))

    def remote_head(self, where: Path, branch: str) -> str | None:
        return self.commit_at(where, f"refs/remotes/origin/{branch}")

    def git_path(self, where: Path, name: str) -> Path:
        """The path of `name` in the git folder of the worktree `where`."""
        return Path(self.said(where, "rev-parse", ABSOLUTE, "--git-path", name))


def commit_of(line: str) -> Commit:
    """One line of `LOG` as a commit."""
    sha, parents, subject = line.split("\t", 2)
    return Commit(sha=sha, parents=tuple(parents.split()), subject=subject)


def counted(number: str) -> int:
    """A count of `--numstat`; a binary file's `-` counts no line."""
    return int(number) if number.isdigit() else 0


def conflicted(lines: list[str]) -> list[str]:
    """The files `git merge-tree --name-only` names after the tree, up to its blank line."""
    named = lines[1:]
    return named[: named.index("")] if "" in named else named
