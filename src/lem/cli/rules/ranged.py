"""The files a range of commits changes, through the `Git` port: `BASE..TIP`, or `BASE...TIP`
from the commit the two share. A side left out is HEAD, as git reads it."""

import os
from typing import TYPE_CHECKING

from lem.app import wiring
from lem.cli.rules.renames import unfolded
from lem.kernel import paths
from lem.kernel.errors import Refusal
from lem.ports.place import Place

if TYPE_CHECKING:
    from pathlib import Path

    from lem.ports.git import GitFacts
    from lem.store.places import Workspace

TWO_DOTS = ".."
THREE_DOTS = "..."
HEAD = "HEAD"
RANGE = "range"
FIX = "name a range of commits this repository holds: BASE..TIP"


def range_names(space: Workspace, root: Path, commits: str) -> tuple[str, ...]:
    """The paths the range `commits` changes in the checkout `root`, a moved file under both
    its names."""
    git = git_of(space)
    since, until = ends(git, root, commits)
    listed = git.diff_stat(root, since, until).paths
    return tuple(name for shown in listed for name in unfolded(shown))


def git_of(space: Workspace) -> GitFacts:
    """The `Git` port, bound for this call."""
    environ = os.environ
    place = Place(checkout=space.checkout, home=paths.home(environ), environ=environ)
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
