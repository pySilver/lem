"""Why the merge's confirm step has nothing to do now (`board_task.merge_step` and
`board_model.stands_said` on `main`): the owner's merge stands, the task is not open, Lem lands it
again on the moved base, or the forge calls it conflicting."""

from typing import TYPE_CHECKING

from lem.board.views import offers
from lem.model.landing import merge_standing
from lem.model.owner import merging

if TYPE_CHECKING:
    from lem.board.views.standing import Standing
    from lem.board.views.world import Seen, World
    from lem.records.record import Record

READS = (
    "Your merge stands. It goes through when the merge agent’s read of the new base says "
    "safe."
)
MERGES = "Your merge stands. Lem merges it now."
RELANDS = (
    "Lem lands it again: the base moved after the checks ran, so a merge now is refused "
    "the same way. The task’s session lands it again, and its new proposal is open for a "
    "merge."
)
CONFLICT = (
    "The forge calls its pull request conflicting with the base: Lem brings it onto the "
    "base first, and then it waits for you again."
)


def why_not(world: World, seen: Seen, standing: Standing) -> str | None:
    """Why there is nothing to merge now, or None while the board offers the merge."""
    record = seen.record
    conflict = record.task.slug in world.forge.conflicts
    stands = merge_standing.standing_of(record)
    if stands is not None and not conflict:
        return READS if refused_for_base(record) else MERGES
    if offers.merge_offered(seen, conflicts=world.forge.conflicts):
        return None
    if record.task.status != "open":
        label = standing.label.lower()
        return f"Nothing to merge now: the task is {label}."
    if merging.merge_wait(record) == "relands":
        return RELANDS
    return CONFLICT


def refused_for_base(record: Record) -> bool:
    """Whether Lem refused the owner's merge of the proposed tip because the base moved."""
    landing = record.landing
    refused = landing.refused if landing else None
    proposed = landing.proposed if landing else None
    if refused is None or proposed is None:
        return False
    lems = refused.source == "lem" and refused.kind == "base"
    return lems and refused.by == "owner" and refused.tip == proposed.tip
