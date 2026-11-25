"""`merged` taken beside the due step of a new round: the pull request on record was closed on
the forge meanwhile, which `propose` refuses, naming `lem land merged` (`main:land.cmd_merged`
took an open or a landing task with a pull request)."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lem.app.landing.frame import Context
    from lem.model.landing.world import Due

# The steps of a round that prepares a proposal.
PREPARING = frozenset(("start", "base", "polish", "checks", "read", "file", "propose"))


def admits(context: Context, due: Due) -> bool:
    """Whether the request on record is closed on the forge while a new round prepares."""
    pull, landing = context.world.pull, context.record.landing
    if due.step not in PREPARING or landing is None or landing.pull is None:
        return False
    return pull is not None and pull.state == "closed"
