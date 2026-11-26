"""What a run of the checks refuses after its commands ran (`land.checks_body` on `main`): a
command that changed the tree it judged, or red commands. A builder repairs the change,
and the checks are never edited to pass. A worktree of the criteria's check that stays is a
line with the command that removes it.
"""

import shlex
from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from pathlib import Path

SHORT = 9
AGAIN = "then run `lem land checks {slug}` again"


def tree_moved(slug: str, worktree: str, changed: str) -> Refusal:
    """A command of the checks changed what git tracks: its result is about another tree."""
    again = AGAIN.format(slug=slug)
    return Refusal(
        "tracked-change",
        "a command of the checks changed what git tracks, so its result is about another "
        f"tree:\n{changed}",
        f"put the files back (`git -C {shlex.quote(worktree)} checkout -- FILE`) and make "
        f"the command change no tracked file, {again}",
    )


def committed(slug: str, worktree: str, tip: str, moved: str) -> Refusal:
    """A command of the checks made a commit on the branch."""
    again = AGAIN.format(slug=slug)
    before, after = tip[:SHORT], moved[:SHORT]
    commits = f"{before}..{after}"
    return Refusal(
        "tracked-change",
        f"a command of the checks made a commit on the branch ({commits}), so its result "
        "is about another tree",
        "make the command commit nothing, put the branch back with "
        f"`git -C {shlex.quote(worktree)} reset --hard {tip}`, {again}",
    )


def stuck(place: Path, checkout: Path) -> str:
    """The line of a worktree of the criteria's check that could not be removed, with the
    command that removes it, its paths quoted for the shell (`criteria.remove` on `main`)."""
    words = ("worktree", "remove", "--force", "--force", str(place))
    command = shlex.join(("git", "-C", str(checkout), *words))
    return f"{place} could not be removed; remove it yourself: {command}"


def red(failed: tuple[str, ...]) -> Refusal:
    """The checks are red on these commands."""
    named = "; ".join(failed)
    return Refusal(
        "red",
        f"the checks are red on {len(failed)} command(s): {named}",
        "a builder reads the output files and repairs the change; the checks are never "
        "edited to pass",
    )
