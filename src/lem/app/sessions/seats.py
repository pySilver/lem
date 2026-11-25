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
from typing import TYPE_CHECKING, Literal

from msgspec.structs import replace

from lem.app.sessions import seating
from lem.records.holds import Blocked
from lem.records.journal.task import StateNoted
from lem.store import tasks

if TYPE_CHECKING:
    from lem.app.sessions.here import Here
    from lem.records.record import Record
    from lem.records.work import StandIn

type Failing = Literal["reviewer", "planner", "merger"]
type Error = Literal["missing", "login", "tokens", "model"]
STAND_IN = "stand-in"
# Each error's words in the line of a stand-in or a block (`state.SEAT_ERRORS` on `main`).
ERRORS = (
    ("missing", "its program is not on this Mac"),
    ("login", "it is not logged in"),
    ("tokens", "it has no tokens left"),
    ("model", "it does not know the model"),
)


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
    return seating.parsed(held.took, role, f"the stand-in of {role}", STAND_IN)


def failed(here: Here, slug: str, failure: StandIn) -> Record:
    """Put a seat's error on the task's record: the fallback stands in, or the task is
    blocked."""
    seating.parsed(failure.failed, failure.seat, "--seat", "--seat")
    fallback = seating.seat_of("fallback", here.where.checkout, here.home)
    took = replace(failure, took=took_seat(failure, fallback))
    record = tasks.read(here.where.state, slug)
    change = partial(with_failure, failure=took, line=said(took))
    return tasks.update(here.where.state, slug, change, record.revision)


def took_seat(failure: StandIn, fallback: seating.Shown) -> str | None:
    """The fallback's seat when it may stand in, else None: it is off, it is the seat that
    failed, or its agent may not sit in the seat."""
    agents, _, _ = seating.ROLES[failure.seat]
    if fallback.seat is False or fallback.seat == failure.failed:
        return None
    return fallback.seat if fallback.agent in agents else None


def with_failure(record: Record, *, failure: StandIn, line: str) -> Record:
    """The record with the stand-in, or with the block when no fallback took the seat."""
    task = record.task
    held = None if failure.took else "blocked"
    entry = StateNoted(at=failure.at, status=task.status, hold=held, line=line)
    if held:
        task = replace(task, hold=blocked(task.slug, failure, line))
    changed = replace(task, stand_ins=(*task.stand_ins, failure))
    return replace(record, task=changed, journal=(*record.journal, entry))


def blocked(slug: str, failure: StandIn, line: str) -> Blocked:
    """The block of a seat no fallback could take."""
    fix = f"lem seat again {slug} once the owner has fixed it"
    return Blocked(why=line, fix=fix, seat=failure.seat, since=failure.at)


def said(failure: StandIn) -> str:
    """The line of a seat's error: the stand-in that took its place, or why none could."""
    why = dict(ERRORS)[failure.error]
    head = f"the {failure.seat}'s seat `{failure.failed}` gave an error: {why}"
    if failure.took is not None:
        return (
            f"{head}; `{failure.took}` stands in for it, and the pull request says so"
        )
    return f"{head}, and no fallback may stand in for it"
