"""A task waits for the repair of a red base, then starts its landing again."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel.errors import Refusal
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


def after_of(record: Record) -> tuple[str, ...]:
    """The tasks the record's task waits for: the `after` of a queued task, and the repair a
    task blocked because the base is red waits for (`land.waited_for` on `main`)."""
    task = record.task
    if task.status == "queued":
        return task.after
    repair = dependency(task)
    return (repair,) if repair else ()


def way_on(slug: str, after: str) -> str:
    """How the landing goes on after the repair or on the owner's word."""
    command = f'lem task move {slug} ready --line "the base is green again"'
    return f"after {after} lands or on the owner's word, {command} clears the hold"


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
    fix = way_on(task.slug, after)
    hold = Blocked(why=WHY, fix=fix, since=now, after=after)
    entry = StateNoted(at=now, status="ready", hold="blocked", line=WHY)
    return replace(
        record,
        task=replace(task, status="ready", hold=hold, since=now),
        journal=(*record.journal, entry),
    )
