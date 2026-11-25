"""The facts of a worktree that the checks read and the `Git` port does not give yet: what git
neither tracks nor ignores, what it ignores, the status of what it tracks, and a path's kind at
a commit (`land.untracked`, `stale_bytecode` and `criteria.cmd_red` on `main`).

A stand-in until the port has them (`notes/land-checks.md`): each runs git through the git
adapter's own shell, with the environment the command started with. Paths of git's `-z`
output are read as bytes and named as the file system names them, never through text mode,
which turns a carriage return in a name into a line end.
"""

import os
import subprocess
from typing import TYPE_CHECKING

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
        words = ran.stderr.decode(errors="replace").strip()
        named = " ".join(args[:2])
        raise Refusal(
            "git",
            f"git {named} failed: {words}",
            "the owner reads git's words, puts the worktree right, and runs the step again",
        )
    entries = ran.stdout.split(b"\0")
    return tuple(os.fsdecode(entry) for entry in entries if entry)


def untracked(where: Path) -> tuple[str, ...]:
    """Each file of the worktree that git neither tracks nor ignores, one by one, a file in a
    new folder too."""
    entries = listed(where, "status", "--porcelain", "--untracked-files=all", "-z")
    return tuple(entry[3:] for entry in entries if entry.startswith("?? "))


def ignored(where: Path) -> tuple[str, ...]:
    """What git ignores in the worktree, a folder whole by its name with its final slash."""
    return listed(
        where,
        "ls-files",
        "--others",
        "--ignored",
        "--exclude-standard",
        "--directory",
        "-z",
    )


def ignored_of(where: Path, folders: tuple[str, ...]) -> frozenset[str]:
    """Which of `folders` a rule ignores. `check-ignore` reads each path as a pathspec, so a
    folder named `:(top)x` would read as `x` at the top; `./` before it makes git read it as it
    is. With no `--no-index`, a folder that holds a tracked file is never named."""
    asked = b"".join(os.fsencode(f"./{folder}\0") for folder in folders)
    named = listed(where, "check-ignore", "--no-index", "--stdin", "-z", asked=asked)
    return frozenset(path.removeprefix("./") for path in named)


def changed(where: Path) -> str:
    """What git tracks that the worktree changed, as `git status --porcelain` says it."""
    ran = raw(where, "status", "--porcelain")
    return ran.stdout.decode(errors="replace").strip()


def kind_at(where: Path, rev: str, path: str) -> str:
    """The kind of `path` at `rev`: `blob`, `tree`, or "" when it holds none. `--`: a name
    that starts with a hyphen is still a name."""
    ran = raw(where, "cat-file", "-t", "--", f"{rev}:{path}")
    return ran.stdout.decode(errors="replace").strip()
