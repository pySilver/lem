"""The checks and merge agent's read that cover the head and base GitHub merged."""

from typing import TYPE_CHECKING

from lem.model.landing import merge_lines
from lem.records.base import Frozen, Sha

if TYPE_CHECKING:
    from lem.model.landing.reconcile import Trees
    from lem.records.landing.merge import Merged
    from lem.records.landing.propose import MergeRead
    from lem.records.landing.record import Landing


class Coverage(Frozen, frozen=True, kw_only=True):
    """The base a review covered and the pull request's line, if any."""

    read: Sha | None = None
    line: str | None = None
    uncovered: bool = False


def reviews(landing: Landing, merged: Merged) -> list[MergeRead]:
    """The merge agent's verdicts on the head GitHub merged, newest first."""
    return [
        read
        for read in reversed(landing.reads)
        if read.tip == merged.merged_head and read.verdict is not None
    ]


def missed_approval(base: str, merged: Merged, checked: Sha) -> Coverage:
    """An approval through Lem needs passed checks on the exact merge parent."""
    return Coverage(
        line=(
            f"The checks ran on {base} at {checked}. GitHub merged on {base} at "
            f"{merged.parent}, which missed the checks for the owner's approval."
        ),
        uncovered=True,
    )


def judged(landing: Landing, merged: Merged, trees: Trees, base: str) -> Coverage:
    """Which evidence covers the merge, and the line of a move or missing evidence."""
    warning = merge_lines.head_warning(landing, merged)
    if warning is not None:
        return Coverage(line=warning, uncovered=True)
    checked = landing.checked
    passed = (
        checked.base if checked is not None and checked.outcome == "passed" else None
    )
    owner_call = merged.by == "owner" and merged.via != "github"
    if passed is not None and owner_call and merged.parent != passed:
        return missed_approval(base, merged, passed)
    if passed is not None and trees.parent == trees.checks:
        return on_checked_tree(reviews(landing, merged), trees.parent)
    return on_other_tree(landing, merged, trees.parent, base, passed)


def on_checked_tree(reads: list[MergeRead], tree: Sha) -> Coverage:
    """The checks cover this base, and an actual verdict may also cover it."""
    read = next((found.base for found in reads if found.base_tree == tree), None)
    return Coverage(read=read)


def on_other_tree(
    landing: Landing, merged: Merged, tree: Sha, base: str, passed: Sha | None
) -> Coverage:
    """Only a safe review covers a base beyond the passed checks."""
    safe = [
        (read, read.why)
        for read in reviews(landing, merged)
        if read.base_call == "safe" and read.why
    ]
    for read, why in safe:
        if read.base_tree == tree:
            return covered_by_read(base, merged.parent, passed, read.base, why)
    if passed is not None:
        previous = safe[0][0].base if safe else None
        line = merge_lines.uncovered_line(base, (passed, merged.parent), previous)
        return Coverage(line=line, uncovered=True)
    return Coverage(
        line=(
            f"GitHub merged on {base} at {merged.parent}. "
            "No passed checks or safe review covered this base."
        ),
        uncovered=True,
    )


def covered_by_read(
    base: str, parent: Sha, passed: Sha | None, reviewed: Sha, why: str
) -> Coverage:
    """The line of a safe review, with the checks' base when they passed."""
    onto = parent[: merge_lines.SHORT]
    line = (
        f"GitHub merged on {base} at {onto}. The merge agent's read covered this base: {why}"
        if passed is None
        else merge_lines.base_line(base, (passed, parent), why)
    )
    return Coverage(read=reviewed, line=line)
