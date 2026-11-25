"""The facts of a change that the bar and the polish pass read and the `Git` port does not give
yet: its diff with no context, its rows of names and status, the paths it changed, the paths a
commit touched, and a file's first line at a commit (`land.check_bar`, `shebang_kinds`,
`changed` and `cmd_polish` on `main`).

A stand-in until the port has them (`notes/land-checks.md`). `-M`: a file that moved is one
file, so its tests are not counted as gone and come again.
"""

import os
import subprocess
from typing import TYPE_CHECKING

from lem.adapters.git_cli_shell import GIT, own
from lem.app.landing import checks_git

if TYPE_CHECKING:
    from pathlib import Path

# The bytes of a file's first line that are read for its `#!`: an interpreter's path and name
# fit in it, and a built file of one long line is never read whole.
FIRST_LINE = 256
DIFF = "diff"


def added(where: Path, base: str, tip: str) -> tuple[str, ...]:
    """The paths the change adds, a moved file as the path that came."""
    return checks_git.listed(
        where, DIFF, "--name-only", "--no-renames", "--diff-filter=A", "-z", base, tip
    )


def diff(where: Path, base: str, tip: str) -> str:
    """`git diff -U0 -M BASE TIP`: every hunk with no line of context."""
    ran = checks_git.raw(where, DIFF, "-U0", "-M", base, tip)
    return ran.stdout.decode(errors="replace")


def rows(where: Path, base: str, tip: str) -> tuple[str, ...]:
    """`git diff --name-status -M`: a status, a path, and a moved file's new path, by tabs."""
    ran = checks_git.raw(where, DIFF, "--name-status", "-M", base, tip)
    return tuple(ran.stdout.decode(errors="replace").splitlines())


def paths(where: Path, base: str, tip: str) -> tuple[str, ...]:
    """Every path that differs between two commits; a rename is the path that went and the
    path that came."""
    return checks_git.listed(
        where, DIFF, "--name-only", "--no-renames", "-z", base, tip
    )


def touched(where: Path, commit: str) -> tuple[str, ...]:
    """The paths one commit changed."""
    return checks_git.listed(
        where,
        "diff-tree",
        "--no-commit-id",
        "--name-only",
        "--no-renames",
        "-r",
        "-z",
        commit,
    )


def first_line(where: Path, tip: str, name: str) -> str:
    """The first line of `name` at `tip`, at most FIRST_LINE bytes of it; "" when `tip`
    holds no such file."""
    with subprocess.Popen(
        [GIT, "-C", str(where), "cat-file", "blob", f"{tip}:{name}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        env=own(os.environ),
    ) as read:
        stream = read.stdout
        first = b"" if stream is None else stream.readline(FIRST_LINE)
        read.kill()
    return first.decode(errors="replace")
