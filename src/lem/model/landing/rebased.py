"""What a rebase showed of the change, from facts: git's merge of the tip before it onto the
base against the tip it made (`land.rebase_unshown` on `main`).

A rebase is shown to keep the change only where that merge is clean and is the new tip's tree,
the same tree id, so the same content and modes. Where it met a conflict, nothing outside its
marks shows which side kept an edit; where the trees differ, the paths that differ say where.
"""

from typing import TYPE_CHECKING

from lem.records.base import Frozen

if TYPE_CHECKING:
    from lem.records.base import Sha
    from lem.records.landing.start import Based

# The first words of why a rebase's tip is not shown to keep the change.
UNSHOWN = "the rebase could not be shown to keep the change"


class Clash(Frozen, frozen=True, kw_only=True):
    """git's merge of two commits met a conflict in these files."""

    files: tuple[str, ...]


# git's merge of two commits: its tree, its conflict, or None where none was asked.
type Merged = Sha | Clash | None
type Paths = tuple[str, ...]


def unshown(merged: Sha | Clash, differ: Paths) -> Paths:
    """The paths where a rebase's tip is not git's merge of the tip before it onto the base:
    each path of the merge's conflict, or each path where the two trees differ."""
    if not isinstance(merged, Clash):
        return differ
    return merged.files or ("a path git did not name",)


def carried(merged: Merged, tree: Sha) -> bool:
    """Whether git's merge of the reviewed tip onto the base is the tip's tree: the review
    carries over the rebase."""
    return isinstance(merged, str) and merged == tree


def why_unshown(based: Based | None) -> str | None:
    """Why the rebase that made the tip showed no carry, for `read` and for the owner's merge
    that `propose` ends; None when it showed what it changed."""
    if based is None or not (based.unshown_paths or based.unshown_commits):
        return None
    paths = ", ".join(based.unshown_paths) or "no path"
    onto = based.base[:9]
    why = f"{UNSHOWN}: git's merge of the tip before it onto {onto} differs in {paths}"
    if not based.unshown_commits:
        return why
    left = ", ".join(sha[:9] for sha in based.unshown_commits)
    return (
        f"{why}; the rebase left out each commit whose patch the base holds: {left}, and "
        "`git cherry-pick HASH` brings one back if the base took it out again"
    )
