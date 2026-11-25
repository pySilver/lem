"""The facts of paths of the `Git` port through real git (`GitChanges`): the files of a folder at a
commit, the paths a range changed, and the commits a base holds already by their patch. Names are
read as git wrote them (`-z`) and shown as `git_cli_names` shows them."""

from typing import TYPE_CHECKING

from lem.adapters.git_cli_facts import commit_of
from lem.adapters.git_cli_names import listed
from lem.adapters.git_cli_shell import GIT, Shell
from lem.ports.faults import Unanswered

if TYPE_CHECKING:
    from pathlib import Path

    from lem.ports.git_facts import Commit

# `git log --cherry-mark`'s mark of a commit whose patch the other side holds, before the fields
# of `git_cli_facts.LOG`.
SAME = "="
MARKED = "--format=%m%x09%H%x09%P%x09%an%x09%s"


class Changes(Shell):
    """The files under a folder at a commit, the paths of a range, and the commits a rebase
    leaves out because the base holds their patch."""

    def files(self, where: Path, rev: str, folder: str) -> tuple[str, ...]:
        named = ("ls-tree", "-r", "--name-only", "-z", "--full-tree", rev, "--", folder)
        return tuple(sorted(self.names(where, *named)))

    def changed_paths(self, where: Path, since: str, until: str) -> tuple[str, ...]:
        named = ("diff", "--name-only", "--no-renames", "-z", since, until)
        return self.names(where, *named)

    def left_out(self, where: Path, onto: str, tip: str) -> tuple[Commit, ...]:
        marks = ("log", "--cherry-mark", "--right-only", "--no-merges", "--reverse")
        span = f"{onto}...{tip}"
        return same_patch(self.said(where, *marks, MARKED, span))

    def names(self, where: Path, *args: str) -> tuple[str, ...]:
        """The names of a `-z` list git gives for `args`, each shown once."""
        ran = self.raw(where, *args)
        if ran.returncode:
            said = ran.stderr.decode(errors="replace").strip()
            raise Unanswered(GIT, said or f"git exited {ran.returncode}")
        return listed(ran.stdout)


def same_patch(found: str) -> tuple[Commit, ...]:
    """The commits of a `MARKED` log whose patch the other side holds, in its order."""
    lines = (line.split("\t", 1) for line in found.splitlines() if line)
    same = (rest for mark, rest in lines if mark == SAME)
    return tuple(map(commit_of, same))
