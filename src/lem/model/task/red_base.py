"""A task waits for the repair of a red base, then starts its landing again."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.task import holds
from lem.records.holds import Blocked
from lem.records.journal.task import StateNoted

if TYPE_CHECKING:
    from lem.records.base import Moment
    from lem.records.record import Record
    from lem.records.task import Task

WHY = "the base is red"


def dependency(task: Task) -> str | None:
    """The repair a red-base block waits for."""
    hold = task.hold
    if isinstance(hold, Blocked) and hold.why == WHY:
        return hold.after
    return None


def command(slug: str) -> str:
    """The command that lifts the block after the repair lands."""
    return f"lem task red-base {slug}"


def blocked(record: Record, repair: Record, now: Moment) -> Record:
    """Keep the repair as a dependency and bring the task back to ready."""
    task, after = record.task, repair.task.slug
    if dependency(task) == after:
        return record
    if task.status != "landing" or task.hold is not None or task.slug == after:
        raise Refusal(
            "red-base",
            "only a landing with no hold can wait for a red-base repair in another task",
            "give the task in its landing and the separate task that repairs the base",
        )
    fix = f"after {after} lands, {command(task.slug)} clears the block"
    hold = Blocked(why=WHY, fix=fix, since=now, after=after)
    entry = StateNoted(at=now, status="ready", hold="blocked", line=WHY)
    return replace(
        record,
        task=replace(task, status="ready", hold=hold, since=now),
        journal=(*record.journal, entry),
    )


def needs_repair(record: Record) -> str:
    """The repair of a task held for a red base."""
    after = dependency(record.task)
    if after is None:
        slug = record.task.slug
        raise Refusal(
            "red-base",
            f"{slug} does not wait for a red-base repair",
            f"lem task show {slug} names its status and hold",
        )
    return after


def released(record: Record, repair: Record, now: Moment) -> Record:
    """Lift the block once the repair lands."""
    status = repair.task.status
    if status != "landed":
        after, slug = repair.task.slug, record.task.slug
        raise Refusal(
            "repair-pending",
            f"{after} is {status}; {slug} waits for it to land",
            f"after {after} lands, {command(slug)} clears the block",
        )
    return holds.moved(record, status="ready", line="the base is green again", now=now)
