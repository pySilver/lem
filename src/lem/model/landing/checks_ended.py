"""What a run of the checks refuses after its commands ran (`land.checks_body` on `main`): a
command that changed the tree it judged, red commands, and the criteria's check that did not
hold. Each is the step's exit 1, with the run on record; a builder repairs it, and the checks
are never edited to pass.
"""

from lem.kernel.errors import Refusal

SHORT = 9
AGAIN = "then run `lem land checks {slug}` again"


def tree_moved(slug: str, worktree: str, changed: str) -> Refusal:
    """A command of the checks changed what git tracks: its result is about another tree."""
    again = AGAIN.format(slug=slug)
    return Refusal(
        "tracked-change",
        "a command of the checks changed what git tracks, so its result is about another "
        f"tree:\n{changed}",
        f"put the files back (`git -C {worktree} checkout -- FILE`) and make the command "
        f"change no tracked file, {again}",
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
        f"make the command commit nothing, put the branch back with `git -C {worktree} "
        f"reset --hard {tip}`, {again}",
    )


def red(failed: tuple[str, ...]) -> Refusal:
    """The checks are red on these commands."""
    named = "; ".join(failed)
    return Refusal(
        "red",
        f"the checks are red on {len(failed)} command(s): {named}",
        "a builder reads the output files and repairs the change; the checks are never "
        "edited to pass",
    )


def criteria(why: str) -> Refusal:
    """The check of the criteria did not hold: in the words it gave."""
    return Refusal(
        "criteria",
        why,
        "a builder repairs the test or the plan; the check is never edited to pass",
    )
