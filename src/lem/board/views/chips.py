"""The chips of a task's card that a developer acts on (`board_pages.card_chips` on `main`): the
type of the request, who works on it, careful, the breaker that waits, a session it lacks, red
checks, a review that was not clean, green or not green, and the pull request."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.board.inputs import names
from lem.board.inputs.parts import Chip
from lem.board.views import marks
from lem.records.decisions import Breaker
from lem.records.holds import BreakerHold
from lem.records.journal.landing import CarefulMissed

if TYPE_CHECKING:
    from lem.board.views.world import Seen
    from lem.records.record import Record
    from lem.model.owner.looks import Row
    from lem.records.task import Task

TYPE = "The type of the request, as Lem took it from the request: {kind}, because {why}"
# Who works on a task, as a chip says it: the fast track's one builder, and the plan talk.
LEADS = MappingProxyType(
    {
        "small": (
            "fast track",
            "code",
            (
                "The fast track: one builder makes it, with no lead and no plan, and "
                "the landing checks it"
            ),
        ),
        "session": (
            "plan talk",
            "table-columns",
            (
                "A companion session talks the plan through, with the reviewer in its "
                "other pane; an agent builds it after the talk"
            ),
        ),
    }
)
# Why a breaker stopped the build, in the words of the owner who approved the criteria.
BREAKS = MappingProxyType(
    {
        "irreversible": "the next step cannot be undone by a later “no”",
        "criteria": "no option keeps the criteria you approved",
    }
)
ALERT = "triangle-exclamation"


def chips(seen: Seen, rows: tuple[Row, ...]) -> tuple[Chip, ...]:
    """The card's chips, in their order."""
    task = seen.record.task
    found = (
        kind_chip(task),
        lead_chip(task),
        careful(seen.record),
        breaker_chip(task),
        marks.session(rows),
        marks.checks(seen.record),
        marks.review(seen.record),
        marks.verdict(seen.record),
        pull_chip(seen),
    )
    return tuple(chip for chip in found if chip is not None)


def kind_chip(task: Task) -> Chip | None:
    """The type of the request."""
    shape = task.shape
    if shape is None:
        return None
    title = TYPE.format(kind=shape.type, why=shape.why)
    return Chip(label=shape.type, icon="flag", title=title)


def lead_chip(task: Task) -> Chip | None:
    """The fast track or the plan talk, which moves while the task builds."""
    lead = LEADS.get(task.lead or "")
    if lead is None:
        return None
    label, icon, title = lead
    live = task.status == "building"
    return Chip(label=label, icon=icon, look="lead", title=title, live=live)


def breaker_chip(task: Task) -> Chip | None:
    """The breaker that waits for the owner."""
    hold = task.hold
    if not isinstance(hold, BreakerHold):
        return None
    breakers = (one for one in task.decisions if isinstance(one, Breaker))
    breaker = next((one for one in breakers if one.id == hold.number), None)
    if breaker is None:
        return None
    cause = BREAKS[breaker.cause]
    title = f"Breaker {breaker.id}: {breaker.what}\n{cause}"
    return Chip(
        label=f"breaker {breaker.id} waits",
        icon=ALERT,
        look="you",
        title=title,
        live=True,
    )


def pull_chip(seen: Seen) -> Chip | None:
    """The pull request, which links to it."""
    landing = seen.record.landing
    if landing is None or landing.pull is None:
        return None
    return names.pull_chip(landing.pull)


def careful(record: Record) -> Chip | None:
    """Careful, by the review's newest call or by a review the plan's call missed."""
    missed = [entry for entry in record.journal if isinstance(entry, CarefulMissed)]
    if missed:
        why = missed[-1].why
        return careful_chip(
            f"the review called it careful, and the plan did not: {why}"
        )
    reviews = record.landing.reviews if record.landing else ()
    called = [one for one in reviews if one.careful is not None]
    newest = called[-1] if called else None
    if newest is None or not newest.careful:
        return None
    why = newest.careful_why or ""
    return careful_chip(f"the review of round {newest.attempt}: {why}")


def careful_chip(by: str) -> Chip:
    """The chip of a careful change."""
    title = f"Careful, by {by}"
    return Chip(label="careful", icon="shield-exclamation", look="you", title=title)
