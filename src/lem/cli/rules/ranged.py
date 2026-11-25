"""The files a range of commits changes: `BASE..TIP`, or `BASE...TIP` from the commit the two
share. A side left out is HEAD, as git reads it.

The two ends are the `Git` port's facts. The names come from `git diff --name-only --no-renames
-z` itself, as on `main`: a moved file under its old name and its new one, and each name as git
keeps it, with no quoting and no short form to read back (an arrow in a name is part of the
name). The port has no such fact yet (`notes/settings.md`, for `core`).
"""

import os
import subprocess
from typing import TYPE_CHECKING

from lem.app import wiring
from lem.kernel import paths
from lem.kernel.errors import Refusal
from lem.ports.place import Place

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from lem.ports.git import GitFacts

TWO_DOTS = ".."
THREE_DOTS = "..."
HEAD = "HEAD"
RANGE = "range"
FIX = "name a range of commits this repository holds: BASE..TIP"
# What would send git to another repository than the one named.
AIMED = frozenset(("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE"))
# A diff of names takes far less than this (unmeasured estimate).
TIMEOUT = 120
DIFF = ("diff", "--name-only", "--no-renames", "-z")


def range_names(root: Path, commits: str) -> tuple[str, ...]:
    """The paths the range `commits` changes in the checkout `root`, a moved file under both
    its names."""
    environ = os.environ
    git = git_of(root, environ)
    since, until = ends(git, root, commits)
    return changed(root, (since, until), environ)


def changed(
    root: Path, between: tuple[str, str], environ: Mapping[str, str]
) -> tuple[str, ...]:
    """The names `git diff --name-only --no-renames -z` gives between two commits."""
    ran = subprocess.run(
        ["git", "-C", str(root), *DIFF, *between],
        capture_output=True,
        env=own(environ),
        stdin=subprocess.DEVNULL,
        timeout=TIMEOUT,
        check=False,
    )
    if ran.returncode:
        words = os.fsdecode(ran.stderr).strip()
        asked = " ".join(between)
        raise Refusal(RANGE, f"git diff {asked} failed: {words}", FIX)
    listed = ran.stdout.split(b"\0")
    return tuple(os.fsdecode(name) for name in listed if name)


def own(environ: Mapping[str, str]) -> dict[str, str]:
    """The call's environment without what would aim git at another repository."""
    return {name: said for name, said in environ.items() if name not in AIMED}


def git_of(root: Path, environ: Mapping[str, str]) -> GitFacts:
    """The `Git` port, bound for this call."""
    place = Place(checkout=root, home=paths.home(environ), environ=environ)
    return wiring.bound(place).git


def ends(git: GitFacts, where: Path, commits: str) -> tuple[str, str]:
    """The two commits the range `commits` runs between, each one git knows."""
    if THREE_DOTS in commits:
        first, second = sides(commits, THREE_DOTS)
        tip = known(git, where, second)
        base = git.merge_base(where, known(git, where, first), tip)
        if base is None:
            raise Refusal(RANGE, f"{first} and {second} share no commit", FIX)
        return base, tip
    if TWO_DOTS in commits:
        first, second = sides(commits, TWO_DOTS)
        return known(git, where, first), known(git, where, second)
    raise Refusal(RANGE, f"{commits} is no range of commits", FIX)


def sides(commits: str, dots: str) -> tuple[str, str]:
    """The two sides of a range, HEAD for a side left out."""
    first, _, second = commits.partition(dots)
    return first or HEAD, second or HEAD


def known(git: GitFacts, where: Path, ref: str) -> str:
    """The commit `ref` names, or a refusal when git knows none."""
    found = git.tip(where, ref)
    if found is None:
        raise Refusal(RANGE, f"git knows no commit {ref}", FIX)
    return found
