"""`lem task resume`: the owner's word to go on with a task he put aside (`stages/park.md`).

A parked task comes back as it was. A dropped task goes on in a new task: from its breaker's
handoff, or, when the release stop dropped it, as a new request on this release. A dropped task
whose journal retention folded into its summary is refused with its ask: the files a new task
would go on from are gone.
"""

from typing import TYPE_CHECKING

from lem.app.tasks import goes_on, park, release, tracker
from lem.kernel.errors import Refusal
from lem.records.decisions import Breaker, Taken
from lem.records.holds import Parked, ReleaseHold
from lem.records.journal.task import Summary
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record


def waiting_breaker(record: Record) -> Breaker | None:
    """The newest breaker of the task that no help of the owner's answered."""
    decisions = record.task.decisions
    helped = {one.breaker for one in decisions if isinstance(one, Taken)}
    breakers = [one for one in decisions if isinstance(one, Breaker)]
    return next((one for one in reversed(breakers) if one.id not in helped), None)


def refusal(record: Record, why: str) -> Refusal:
    """The refusal of a resume, with the way on."""
    slug, ask = record.task.slug, record.task.ask
    return Refusal(
        "resume", f"{slug} {why}", f"new work for it is a new ask: /lem {ask}"
    )


def dropped(where: places.Workspace, record: Record) -> park.Resumed:
    """The resume of a dropped task: a new task that goes on from it."""
    if any(isinstance(entry, Summary) for entry in record.journal):
        raise refusal(
            record,
            "was dropped long ago: its journal became one summary past state.keep_days, "
            "and the files a new task would go on from are gone",
        )
    kind = tracker.kind_of(where.checkout)
    if isinstance(record.task.hold, ReleaseHold):
        return goes_on.as_request(where, record, kind)
    breaker = waiting_breaker(record)
    handoff = places.task_folder(where.state, record.task.slug) / "handoff.md"
    if breaker is None or not handoff.is_file():
        raise refusal(
            record,
            "was dropped with no breaker that waits and its handoff beside it, so there is "
            "no talk to go back to",
        )
    return goes_on.as_breaker(where, record, breaker, kind)


def resumed(folder: Path, slug: str) -> park.Resumed:
    """Bring back the parked task `slug`, or go on from the dropped one."""
    where = places.workspace(folder)
    status = tasks.read(where.state, slug).task.status
    record = release.checked(where.state, slug, ends=status == "dropped")
    if isinstance(record.task.hold, Parked):
        return park.brought_back(where, record)
    if status == "dropped":
        return dropped(where, record)
    ended = status in {"landed", "answered"}
    raise Refusal(
        "resume",
        f"{slug} is {status}: lem task resume takes a parked task or a dropped one",
        "an ended task stays ended, and new work for it is a new ask (/lem new)"
        if ended
        else f"{slug} goes on as it is",
    )
