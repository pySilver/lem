"""The lines a merge and its cleanup leave for the owner: a merge on a base that moved after
the checks, or on a base nothing covered; the squash's body; a branch rebased after its push,
or changed after it, or not merged (`main:land.base_line`, `uncovered_line`, `noted_body`,
`squash_body`, `after_push`, `cmd_clean`)."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lem.records.landing.merge import Merged
    from lem.records.landing.record import Landing

SHORT = 9
# Two commits, in the order a line names them.
type Pair = tuple[str, str]


def base_line(base: str, bases: Pair, why: str) -> str:
    """The line of a merge on a base that moved after the checks, which a safe read covered:
    the base the checks ran on and the base it merged on (`bases`), and the read's why."""
    ran, merged = (sha[:SHORT] for sha in bases)
    return (
        f"The checks ran on {base} at {ran}; it merged on {base} at {merged}, after the "
        f"merge agent's read of what moved: {why}"
    )


def uncovered_line(base: str, bases: Pair, read: str | None) -> str:
    """The line of a merge whose base on the forge neither the checks nor a read covered: a
    merge on GitHub came between Lem's look at the base and the merge, and nothing undoes
    it. `bases` are the checks' base and the base it merged on; `read` the base a read
    covered, if one did."""
    ran, merged = (sha[:SHORT] for sha in bases)
    read_short = read[:SHORT] if read else None
    covered = f" (its read covered {read_short})" if read_short else ""
    return (
        f"The checks ran on {base} at {ran}; it merged on {base} at {merged}, which no read "
        f"of the merge agent covered{covered}: a merge on GitHub came between Lem's look at "
        "the base and its merge, and nothing undoes it"
    )


def noted_body(body: str, line: str) -> str | None:
    """The pull request's text `body` with `line` at its end, once; None when it holds the
    line already, so a second edit is no edit."""
    if line in body:
        return None
    kept = body.rstrip("\n")
    return f"{kept}\n\n{line}\n" if kept else f"{line}\n"


def squash_body(slug: str, moved: str | None) -> str:
    """The body of the one commit a squash makes: the line of a merge on a moved base, when
    there is one, and last the line `Lem task: SLUG` by which the board names the task."""
    named = f"Lem task: {slug}"
    return f"{moved}\n\n{named}" if moved else named


def after_push(branch: str, shas: Pair, bases: Pair, *, same: bool) -> str:
    """The line of a branch rebased after Lem's last push (`shas`: its tip and the head the
    forge merged; `bases`: the tip's base and the merged head's): it holds the same change,
    or it was changed after the push, with the commands that show the difference and remove
    the branch."""
    tip, head = (sha[:SHORT] for sha in shas)
    if same:
        return (
            f"{branch} was rebased after its push: its tip {tip} holds the same change as "
            f"{head}, the head Lem pushed, which the forge merged"
        )
    base_tip, base_merged = (sha[:SHORT] for sha in bases)
    return (
        f"{branch} was changed after its push: the forge merged {head}, the head Lem pushed, "
        f"and the tip {tip} differs from it. `git range-diff {base_merged}..{head} "
        f"{base_tip}..{tip}` shows the difference, and `git branch -D {branch}` removes it"
    )


def unmerged_why(base: str, branch: Pair, *, after: bool, inside: bool) -> str:
    """Why a landed branch (`branch`: its name and tip) stays: origin's `base` does not hold
    its tip, and it has commits `after` the merged head, or the forge merged a head made after
    the tip (`inside`, its "Update branch"), or neither."""
    name, tip = branch
    if after:
        how = "the branch has commits after the head the forge merged"
    elif inside:
        how = 'the forge merged a commit made after its tip (its "Update branch")'
    else:
        how = "the forge did not merge its tip"
    return (
        f"origin's {base} does not hold the tip {tip} of {name}: {how}; the branch and the "
        "forge's copy stay, and nothing was removed"
    )


def head_warning(landing: Landing, merged: Merged) -> str | None:
    """The coverage warning when GitHub merged a different tip."""
    expected = landing.intent or landing.accepted or landing.proposed
    if expected is None or merged.merged_head == expected.tip:
        return None
    tip = expected.tip
    reviewed = any(
        read.tip == tip and read.verdict is not None for read in landing.reads
    )
    line = f"The review covered tip {tip}." if reviewed else f"Lem expected tip {tip}."
    head = merged.merged_head
    return f"{line} GitHub merged a different head, {head}."
