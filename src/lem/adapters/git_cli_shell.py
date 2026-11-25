"""How the `git` adapter runs git: one process for each call, in the folder named, with nothing
on its standard input and the environment of the call (`Place.environ`).

A call that git answers with an exit code the caller reads goes through `tried`; one that must
succeed goes through `said`, and a failure there raises `Unanswered` with git's own words.
"""

import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING

from lem.ports.faults import Unanswered

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

# The longest a git call may take before it counts as no answer, in seconds: a fetch of a
# large repository on a slow link (unmeasured estimate).
TIMEOUT = 300
GIT = "git"
QUIET = "--quiet"
AIMED = frozenset(("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE"))


@dataclass(frozen=True, kw_only=True, slots=True)
class Shell:
    """The environment every git of this adapter runs with."""

    environ: Mapping[str, str]

    def tried(self, where: Path, *args: str) -> subprocess.CompletedProcess[str]:
        """`git -C WHERE ARGS`, whatever its exit code."""
        try:
            return subprocess.run(
                [GIT, "-C", str(where), *args],
                capture_output=True,
                text=True,
                env=own(self.environ),
                stdin=subprocess.DEVNULL,
                timeout=TIMEOUT,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise Unanswered(GIT, str(error)) from error

    def said(self, where: Path, *args: str) -> str:
        """The output of `git -C WHERE ARGS`, without its last line end; a failure is
        `Unanswered` with git's words."""
        ran = self.tried(where, *args)
        if ran.returncode:
            raise Unanswered(GIT, last_words(ran))
        return ran.stdout.rstrip("\n")

    def commit_at(self, where: Path, rev: str) -> str | None:
        """The commit `rev` names in `where`, or None when it names none."""
        ran = self.tried(where, "rev-parse", "--verify", QUIET, f"{rev}^{{commit}}")
        return ran.stdout.strip() or None

    def head(self, where: Path) -> str:
        """The commit HEAD of `where` is at."""
        found = self.commit_at(where, "HEAD")
        if found is None:
            raise Unanswered(GIT, f"{where} has no commit at HEAD")
        return found

    def blob(self, where: Path, spec: str) -> bytes:
        """The bytes of the object `spec` (`REV:PATH`), as git keeps them."""
        try:
            ran = subprocess.run(
                [GIT, "-C", str(where), "cat-file", "blob", spec],
                capture_output=True,
                env=own(self.environ),
                stdin=subprocess.DEVNULL,
                timeout=TIMEOUT,
                check=True,
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise Unanswered(GIT, str(error)) from error
        return ran.stdout


def own(environ: Mapping[str, str]) -> dict[str, str]:
    """The environment of a call, but what would aim git at another repository than the
    folder named."""
    return {name: word for name, word in environ.items() if name not in AIMED}


def last_words(ran: subprocess.CompletedProcess[str]) -> str:
    """What git said last: the last line of its errors, else of its output, else its code."""
    lines = (ran.stderr or ran.stdout).strip().splitlines()
    return lines[-1].strip() if lines else f"git exited {ran.returncode}"
