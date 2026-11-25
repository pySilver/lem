"""The approved tasks that wait when a server merge calls the forge."""

from typing import TYPE_CHECKING

from lem.app.owner import forge
from lem.board.duties import merge_line
from lem.kernel import clock, errors
from lem.model.landing import merge_standing, phases
from lem.model.owner import merging
from lem.records.holds import ReleaseHold
from lem.store import tasks

if TYPE_CHECKING:
    from lem.board.duties.context import Duty
    from lem.records.landing import merge
    from lem.records.record import Record


def eligible(record: Record, look: forge.Look) -> bool:
    """Whether an approval is still in the merge line."""
    if phases.settled(record) is not None or isinstance(record.task.hold, ReleaseHold):
        return False
    if standing_waits(record):
        return True
    return merging.merge_wait(record) == merging.MERGES and not forge.conflicts(
        look, record
    )


def standing_waits(record: Record) -> bool:
    """A standing approval waits through the base work, unless the checks or forge refuse it."""
    landing = record.landing
    if landing is None or record.task.status not in {"open", "landing"}:
        return False
    if landing.intent is not None:
        return False
    if landing.checked is not None and landing.checked.outcome == "red":
        return False
    refused, proposed = landing.refused, landing.proposed
    if (
        refused is not None
        and proposed is not None
        and refused.tip == proposed.tip
        and (refused.source != "lem" or refused.kind != "base")
    ):
        return False
    return merge_standing.standing_of(record) is not None


def waited(duty: Duty, slug: str, intent: merge.MergeIntent) -> merge_line.Waited:
    """The count and names of the other approved tasks at this call."""
    look = forge.read(duty.state)
    records = tasks.every(duty.state)
    others = (one for one in records if one.task.slug != slug)
    behind = tuple(one.task.slug for one in others if eligible(one, look))
    return merge_line.Waited(
        at=clock.now(),
        task=slug,
        tip=intent.tip,
        by=intent.by,
        waiting=len(behind),
        behind=behind,
    )


def at_call(duty: Duty, slug: str, intent: merge.MergeIntent) -> None:
    """Record the current line while the landing still holds both merge locks."""
    try:
        merge_line.noted(duty.state, waited(duty, slug, intent))
    except (OSError, errors.Refusal, errors.Fault) as error:
        duty.say(f"the merge count for {slug} could not be recorded: {error}")
