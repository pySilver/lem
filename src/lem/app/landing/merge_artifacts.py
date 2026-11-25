"""The backlog items and pictures the merge agent reads for a proposal."""

from typing import TYPE_CHECKING

from lem.app.landing import propose_items

if TYPE_CHECKING:
    from pathlib import Path

    from lem.app.landing.frame import Context
    from lem.records.landing.propose import Proposed

# The board's picture types (`tools/board-kit/entry.js`, PICTURE).
PICTURES = frozenset((".png", ".jpg", ".jpeg", ".gif", ".webp"))


def items_of(context: Context, proposed: Proposed) -> tuple[str, ...]:
    """Each item the proposed tip adds to the backlog, whoever filed it."""
    git, worktree = context.ports.git, context.worktree
    since = git.merge_base(worktree, proposed.base, proposed.tip) or proposed.base
    span = (since, proposed.tip)
    paths = git.diff_stat(worktree, *span).paths
    return tuple(
        sorted(filed.path for filed in propose_items.added(git, worktree, span, paths))
    )


def pictures_of(folder: Path) -> tuple[str, ...]:
    """Each visible picture under `media/`, by its path from the task's folder."""
    pictures = (
        path.relative_to(folder)
        for path in (folder / "media").rglob("*")
        if path.is_file() and path.suffix.lower() in PICTURES
    )
    return tuple(
        sorted(
            str(path)
            for path in pictures
            if not any(part.startswith(".") for part in path.parts)
        )
    )
