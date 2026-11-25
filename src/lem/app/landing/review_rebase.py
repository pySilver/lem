"""Git's review coverage when a review and a rebase share a recorded second."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.model.landing import carry

if TYPE_CHECKING:
    from pathlib import Path

    from lem.model.landing.world import World
    from lem.ports.git import Git
    from lem.records.landing.record import Landing


def gathered(git: Git, where: Path, landing: Landing | None, world: World) -> World:
    """Resolve the order of a rebase and a review with the two trees."""
    if landing is None or landing.based is None or not landing.based.carried:
        return world
    based = landing.based
    review = carry.newest(landing)
    if review is None or based.base != world.base:
        return world
    first = world.item_chain[0] if world.item_chain else world.tip
    if review.at != based.at or first != based.tip:
        return world
    tree = git.tree(where, based.tip)
    if git.merge_tree(where, world.base, review.tip) != tree:
        return world
    return replace(world, rebased_review=review.tip)
