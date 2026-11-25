"""The chips of a task's header (`board_task.tags` on `main`): each says something a developer
acts on. The breaker that stopped it, a session it lacks, who works on it, the task of the plan
that is built now, its criteria, its checks, its newest review, and green or not green."""

from typing import TYPE_CHECKING

from lem.board.inputs.parts import Chip
from lem.board.views import cards, chips, hovers, marks, rounds
from lem.board.views.panel.stopped import stopped
from lem.records.holds import BreakerHold, Parked

if TYPE_CHECKING:
    from lem.board.views.world import Seen
    from lem.model.owner.looks import Rows
    from lem.records.landing.review import Reviewed
    from lem.records.record import Record

CHECK = "check"


def tags(seen: Seen, rows: Rows) -> tuple[Chip, ...]:
    """The header's chips, in their order."""
    record = seen.record
    found = (
        breaker_chip(record),
        marks.session(rows),
        chips.lead_chip(record.task),
        plan_chip(seen),
        criteria_chip(record),
        checks_chip(record),
        review_chip(record),
        marks.verdict(record),
    )
    return tuple(chip for chip in found if chip is not None)


def breaker_chip(record: Record) -> Chip | None:
    """The breaker that stopped the build: it waits, it is parked, or it stays on record."""
    task = record.task
    breaker = stopped(task)
    if breaker is None:
        return None
    title = f"{breaker.what}\n{hovers.stop_words(breaker)}"
    waits = isinstance(task.hold, BreakerHold)
    label = f"breaker {breaker.id}"
    if waits:
        label = f"{label} waits"
    elif isinstance(task.hold, Parked):
        label = f"{label}, parked"
    return Chip(
        label=label,
        icon=marks.ALERT,
        look="you" if waits else None,
        title=title,
        live=waits,
    )


def plan_chip(seen: Seen) -> Chip | None:
    """The task of the plan that is built now."""
    task = seen.record.task
    running = cards.running_task(seen)
    total = task.plan.tasks if task.plan else None
    if task.status != "building" or running is None or not total:
        return None
    title = "The task of the plan that is built now"
    return Chip(label=f"task {running} of {total}", icon="layer-group", title=title)


def criteria_chip(record: Record) -> Chip | None:
    """How many criteria, each with its sentence in the hover."""
    criteria = record.task.criteria.criteria
    if not criteria:
        return None
    count = len(criteria)
    label = "1 criterion" if count == 1 else f"{count} criteria"
    lines = (f"{one.number}. {one.text}" for one in criteria)
    return Chip(label=label, icon="file-lines", title="\n".join(lines))


def checks_chip(record: Record) -> Chip | None:
    """The last run of the checks: green with how many commands, or red."""
    red = marks.checks(record)
    if red is not None:
        return red
    checked = record.landing.checked if record.landing else None
    if checked is None or not checked.outcomes:
        return None
    title = "\n".join(marks.command_line(one) for one in checked.outcomes)
    label = f"checks green: {len(checked.outcomes)}"
    return Chip(label=label, icon=CHECK, look="ok", title=title)


def review_chip(record: Record) -> Chip | None:
    """The newest review: clean, its must-fix, or not reviewed; every round in the hover."""
    reviews = record.landing.reviews if record.landing else ()
    if not reviews:
        return None
    newest = reviews[-1]
    said = review_word(newest)
    title = "\n".join(rounds.line(one) for one in reviews)
    look = "ok" if said == "clean" else "bad"
    return Chip(
        label=f"review {newest.attempt}: {said}", icon="eye", look=look, title=title
    )


def review_word(review: Reviewed) -> str:
    """`clean`, `1 must-fix`, or `not reviewed` for an attempt nobody answered."""
    if not review.answered:
        return "not reviewed"
    if rounds.verdict(review) == rounds.MUST_FIX:
        must = rounds.counts(review)[0]
        return f"{must} must-fix"
    return "clean"
