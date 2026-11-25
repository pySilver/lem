"""The stop of a task two releases back (the owner's ruling of 2026-11-18; `release.stop` on
`main`).

A release reads the records of its own release and of the release just before it (`BEFORE`), and
no older ones. A command on a task begun before `BEFORE` stops with the hold `release`, which a
drop and then a resume clear: the resume starts a new request on this release from the notes
and the branch the task left. A task begun on a newer release is the store's refusal
(`newer-release`): its caller is the older Lem, which writes nothing over it.
"""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.kernel.release import newer
from lem.records.holds import ReleaseHold

if TYPE_CHECKING:
    from lem.records.base import Moment
    from lem.records.record import Record

# The release just before this one. A release moves it (AGENTS.md, "A release"); a unit case
# holds it older than plugin.json.
BEFORE = "0.3.0"


def say(slug: str, began: str, running: str, before: str) -> str:
    """The line the stop says, with the way on."""
    return (
        f"{slug} began on Lem {began}, and Lem {running} reads only tasks begun on "
        f"{before} or {running}. Your branch and its commits stay. /lem drop {slug}, then "
        f"/lem resume {slug}, starts a new task on {running} from that branch and from the "
        "notes the task left."
    )


def stops(record: Record, running: str, before: str) -> bool:
    """Whether a command of Lem `running` stops on this task: it began before `before`."""
    return newer(before, record.release) and not newer(record.release, running)


def held(record: Record, running: str, now: Moment) -> Record:
    """The record with the hold `release`, set once: a task held so already keeps its hold
    and its moment."""
    if isinstance(record.task.hold, ReleaseHold):
        return record
    slug = record.task.slug
    hold = ReleaseHold(
        began=record.release,
        running=running,
        say=say(slug, record.release, running, BEFORE),
        since=now,
    )
    return replace(record, task=replace(record.task, hold=hold))


def refusal(record: Record) -> Refusal:
    """The refusal of a command on a task the stop holds."""
    hold = record.task.hold
    said = hold.say if isinstance(hold, ReleaseHold) else ""
    slug = record.task.slug
    return Refusal(
        "release",
        said,
        f"/lem drop {slug}, then /lem resume {slug}, on the owner's word",
    )


def guard(record: Record) -> Refusal | None:
    """Stop a new act after a read that also permits terminal bookkeeping."""
    return refusal(record) if isinstance(record.task.hold, ReleaseHold) else None
