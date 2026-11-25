"""The facts of a worktree that the checks read and the `Git` port does not give yet: what git
neither tracks nor ignores, the status of what it tracks, a path's kind at a commit, and the text
of any other git that must succeed (`land.untracked`, `stale_bytecode` and `criteria.cmd_red` on
`main`).

A stand-in until the port has them (`notes/land-checks.md`): each runs git through the git
adapter's own shell, with the environment the command started with. Paths of git's `-z`
output are read as bytes and named as the file system names them, never through text mode,
which turns a carriage return in a name into a line end.
"""

import os
import subprocess
from typing import TYPE_CHECKING, NoReturn

from lem.adapters.git_cli_shell import GIT, TIMEOUT, own
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from pathlib import Path

# `check-ignore` ends 1 when it names none of the paths it was asked.
NONE_NAMED = 1


def raw(
    where: Path, *args: str, asked: bytes = b""
) -> subprocess.CompletedProcess[bytes]:
    """`git -C WHERE ARGS` with `asked` on its input, its output as bytes."""
    return subprocess.run(
        [GIT, "-C", str(where), *args],
        input=asked,
        capture_output=True,
        env=own(os.environ),
        timeout=TIMEOUT,
        check=False,
    )


def listed(where: Path, *args: str, asked: bytes = b"") -> tuple[str, ...]:
    """The paths a `-z` call of git names; a failure is refused in git's words."""
    ran = raw(where, *args, asked=asked)
    if ran.returncode not in {0, NONE_NAMED}:
        refused(ran, args)
    entries = ran.stdout.split(b"\0")
    return tuple(os.fsdecode(entry) for entry in entries if entry)


def refused(ran: subprocess.CompletedProcess[bytes], args: tuple[str, ...]) -> NoReturn:
    """Refuse a git that failed, in its words."""
    words = ran.stderr.decode(errors="replace").strip()
    named = " ".join(args[:2])
    raise Refusal(
        "git",
        f"git {named} failed: {words}",
        "the owner reads git's words, puts the worktree right, and runs the step again",
    )


def text(where: Path, *args: str) -> str:
    """What git says for `args`, as text; a failure is refused in git's words."""
    ran = raw(where, *args)
    if ran.returncode:
        refused(ran, args)
    return ran.stdout.decode(errors="replace")


def untracked(where: Path) -> tuple[str, ...]:
    """Each file of the worktree that git neither tracks nor ignores, one by one, a file in a
    new folder too."""
    entries = listed(where, "status", "--porcelain", "--untracked-files=all", "-z")
    return tuple(entry[3:] for entry in entries if entry.startswith("?? "))


def changed(where: Path) -> str:
    """What git tracks that the worktree changed, as `git status --porcelain` says it."""
    return text(where, "status", "--porcelain").strip()


def kind_at(where: Path, rev: str, path: str) -> str:
    """The kind of `path` at `rev`: `blob`, `tree`, or "" when it holds none. `--`: a name
    that starts with a hyphen is still a name."""
    ran = raw(where, "cat-file", "-t", "--", f"{rev}:{path}")
    return ran.stdout.decode(errors="replace").strip()
