"""The approved tasks that wait when a server merge calls the forge."""

from typing import TYPE_CHECKING

from lem.app.owner import forge
from lem.board.duties import merge_line
from lem.kernel import clock, errors
from lem.model.landing import phases
from lem.model.owner import merging
from lem.records.holds import ReleaseHold
from lem.store import tasks

if TYPE_CHECKING:
    from lem.board.duties.context import Duty
    from lem.records.landing import merge
    from lem.records.record import Record


def eligible(record: Record, look: forge.Look) -> bool:
    """Whether an approval is still in the merge line."""
    return (
        phases.settled(record) is None
        and not isinstance(record.task.hold, ReleaseHold)
        and merging.merge_wait(record) == merging.MERGES
        and not forge.conflicts(look, record)
    )


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
