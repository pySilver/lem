"""Git's proof that the commits after the checks only add the items Lem filed."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

if TYPE_CHECKING:
    from pathlib import Path

    from lem.model.landing.world import World
    from lem.ports.git import Git
    from lem.records.landing.checks import Checked

type Span = tuple[str, str]
type Paths = frozenset[str]


def added(git: Git, where: Path, span: Span, paths: Paths) -> bool:
    """Each path in a commit is a recorded item that its parent did not have."""
    changed = git.diff_stat(where, *span).paths
    parent = span[0]
    return (
        bool(changed)
        and paths.issuperset(changed)
        and all(git.show(where, parent, path) is None for path in changed)
    )


def chain(git: Git, where: Path, span: Span, paths: Paths) -> tuple[str, ...]:
    """The checked tip and each item-only commit in order, or no proof."""
    if not git.is_ancestor(where, *span):
        return ()
    proven = [span[0]]
    for commit in git.commits(where, *span):
        parent = proven[-1]
        step = (parent, commit.sha)
        contiguous = commit.parents == (parent,)
        if not contiguous or not added(git, where, step, paths):
            return ()
        proven.append(commit.sha)
    return tuple(proven) if proven[-1] == span[1] else ()


def gathered(git: Git, where: Path, checked: Checked | None, world: World) -> World:
    """Gather the proof only when a check run has recorded items after it."""
    tip = world.tip
    if checked is None or tip is None:
        return world
    if not checked.items_after or tip == checked.tip:
        return world
    paths = frozenset(checked.items_after)
    proven = chain(git, where, (checked.tip, tip), paths)
    return replace(world, item_chain=proven)
