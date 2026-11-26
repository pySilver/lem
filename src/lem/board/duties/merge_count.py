"""The approved tasks that wait when a server merge calls the forge."""

from typing import TYPE_CHECKING

from lem.app.owner import forge, releases
from lem.board import merge_look
from lem.board.duties import forge_look, merge_line
from lem.kernel import clock, errors
from lem.model.landing import merge_recheck, merge_standing, phases
from lem.records.holds import Parked, ReleaseHold
from lem.store import tasks

if TYPE_CHECKING:
    from lem.board.duties.context import Duty
    from lem.model.owner.looks import MergeBasis
    from lem.records.landing import merge
    from lem.records.record import Record


def eligible(
    record: Record,
    look: forge.Look,
    basis: MergeBasis,
    owner_tip: str | None,
) -> bool:
    """Whether an approval is still in the merge line."""
    if (
        isinstance(record.task.hold, Parked | ReleaseHold)
        or phases.settled(record) is not None
    ):
        return False
    if standing_waits(record):
        return True
    approved = board_waits(record, owner_tip) or merge_look.server_merges(record, basis)
    return approved and not forge.conflicts(look, record)


def board_waits(record: Record, owner_tip: str | None) -> bool:
    """A live board approval still waits to reach the forge for its exact tip."""
    landing = record.landing
    if owner_tip is None or record.task.status != "open" or landing is None:
        return False
    proposed = landing.proposed
    return (
        proposed is not None
        and proposed.tip == owner_tip
        and landing.intent is None
        and landing.accepted is None
    )


def standing_waits(record: Record) -> bool:
    """A standing approval waits through the base work, unless the checks or forge refuse it."""
    landing = record.landing
    if landing is None or record.task.status not in {"open", "landing"}:
        return False
    if landing.intent is not None:
        return False
    checked = landing.checked
    if merge_recheck.repair(landing) or (checked and checked.outcome == "red"):
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
    look = forge_look.current(duty)
    records = releases.with_stops(tasks.every(duty.state))
    bases = merge_look.bases_of(duty.here, records)
    approvals = duty.kept.approvals()
    behind = tuple(
        one.task.slug
        for one in records
        if one.task.slug != slug
        and eligible(one, look, bases.for_task(one), approvals.get(one.task.slug))
    )
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
