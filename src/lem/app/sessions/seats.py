"""The seat a task's role takes, the fallback that stands in when its agent gives an error, and
the owner's go on (`project.cmd_seat`, `cmd_seat_failed` and `cmd_seat_again` on `main`).

Every stage that opens a seat's agent takes it from `lem seat show`: the fallback while it stands
in for the task, else the seat the settings name. When a stage sees one of the four errors of a
seat's agent (the program is not on the Mac, no login, no tokens, an unknown model; a slow agent
is none), `lem seat failed` alone decides, in the record's own lock: the fallback stands in for
that seat until the task ends or the owner's go on, and the pull request says so; or, when the
fallback is off, is the seat that failed, or may not sit there, the task is blocked with the
seat named. `lem seat again` clears that block and ends each stand-in of its seat, so that the
seat the settings name opens again.
"""

from functools import partial
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.sessions import seat_lines, seating
from lem.kernel.errors import Refusal
from lem.records.journal.task import StateNoted
from lem.store import tasks

if TYPE_CHECKING:
    from lem.app.sessions.here import Here
    from lem.records.record import Record
    from lem.records.work import StandIn

# The statuses of a task that ended: no seat of it runs any more.
ENDED = frozenset(("landed", "answered", "dropped"))


def standing(record: Record, role: str) -> StandIn | None:
    """The stand-in that holds `role` for the task: its newest with no go on since."""
    held = [one for one in record.task.stand_ins if one.seat == role]
    newest = held[-1] if held else None
    return newest if newest and newest.again is None and newest.took else None


def shown(here: Here, slug: str, role: seating.Role) -> seating.Shown:
    """The seat in use for the task's role: the fallback while it stands in, else the
    settings'."""
    held = standing(tasks.read(here.where.state, slug), role)
    if held is None:
        return seating.seat_of(role, here.where.checkout, here.home)
    return seating.parsed(
        held.took, role, f"the stand-in of {role}", seat_lines.STAND_IN
    )


def failed(here: Here, slug: str, failure: StandIn) -> seat_lines.Decision:
    """Put a seat's error on the task's record: the fallback stands in, or the task is
    blocked; the decision, with its line for the owner."""
    seating.parsed(failure.failed, failure.seat, "--seat", "--seat")
    fallback = seating.seat_of("fallback", here.where.checkout, here.home)
    took = replace(failure, took=took_seat(failure, fallback))
    record = tasks.read(here.where.state, slug)
    tasks.update(
        here.where.state, slug, partial(with_failure, failure=took), record.revision
    )
    return seat_lines.Decision.of(slug, took)


def took_seat(failure: StandIn, fallback: seating.Shown) -> str | None:
    """The fallback's seat when it may stand in, else None: it is off, it is the seat that
    failed, or its agent may not sit in the seat."""
    agents, _, _ = seating.ROLES[failure.seat]
    if fallback.seat is False or fallback.seat == failure.failed:
        return None
    allowed = fallback.agent is not None and fallback.agent in agents
    return fallback.seat if allowed else None


def with_failure(record: Record, *, failure: StandIn) -> Record:
    """The record with the stand-in; with no fallback, the block, unless the task waits for
    the owner already, whose hold stays (the block is on its journal and its stand-ins, and
    his go on clears it). Refused for a task that ended: a late error blocks nothing."""
    task = record.task
    if task.status in ENDED:
        raise Refusal(
            "ended",
            f"{task.slug} is {task.status}: no seat of an ended task runs any more",
            "nothing: the error came after the task's end",
        )
    held = None if failure.took else "blocked"
    entry = StateNoted(
        at=failure.at, status=task.status, hold=held, line=seat_lines.said(failure)
    )
    if held and task.hold is None:
        task = replace(task, hold=seat_lines.blocked(task.slug, failure))
    changed = replace(task, stand_ins=(*task.stand_ins, failure))
    return replace(record, task=changed, journal=(*record.journal, entry))
