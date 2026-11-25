"""Git's proof that a commit only removes the backlog item the task started from."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.model.landing.review import newest

if TYPE_CHECKING:
    from pathlib import Path

    from lem.model.landing.world import World
    from lem.ports.git import Git
    from lem.records.record import Record


def removed(git: Git, where: Path, span: tuple[str, str], item_path: str) -> bool:
    """The tip is a single child of the read tip and only deletes the task's item."""
    commits = git.commits(where, *span)
    parent, tip = span
    if len(commits) != 1 or commits[0].parents != (parent,):
        return False
    return (
        commits[0].sha == tip
        and git.diff_stat(where, *span).paths == (item_path,)
        and git.show(where, span[0], item_path) is not None
        and git.show(where, span[1], item_path) is None
    )


def gathered(git: Git, where: Path, record: Record, world: World) -> World:
    """Read a removal proof up to the tip, or up to the start of a verified filing chain."""
    landing, item_path = record.landing, record.task.backlog_item
    last = newest(landing) if landing else None
    tip = world.item_chain[0] if world.item_chain else world.tip
    if last is None or not item_path or tip is None or last.tip == tip:
        return world
    if git.is_ancestor(where, last.tip, tip) and removed(
        git, where, (last.tip, tip), item_path
    ):
        return replace(world, own_item_removed_from=last.tip)
    return world
