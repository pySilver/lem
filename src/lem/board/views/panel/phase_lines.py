"""The line under each phase of a task's progress card (`board_model.progress_of` on `main`):
what its investigation found, the task of the plan, the checks, the newest review, and green or
not green."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.board.views import rounds, telling
from lem.board.views.panel import plan

if TYPE_CHECKING:
    from lem.records.landing.record import Landing
    from lem.records.record import Record

# The steps of the standard track whose phase has a line.
BUILD, CHECKS, REVIEW, PROPOSED = 2, 3, 4, 5


def line_of(record: Record, step: int, lead: int) -> str:
    """The line under phase `step`, after `lead` phases of an investigation."""
    if step < lead:
        found = record.task.investigation
        call = found.call if found else None
        return telling.CALLS[call] if call else ""
    offset = 2 if record.task.lead == "small" else 0
    return phase_line(record, step - lead + offset)


def phase_line(record: Record, step: int) -> str:
    """The line under a phase of the standard track."""
    if step == BUILD:
        return build_line(record)
    said = LINES.get(step)
    landing = record.landing
    return said(landing) if said and landing else ""


def review_line(landing: Landing) -> str:
    """The newest review's verdict."""
    return rounds.verdict(landing.reviews[-1]) if landing.reviews else ""


def proposed_line(landing: Landing) -> str:
    """Green or not green, once proposed."""
    proposed = landing.proposed
    if proposed is None:
        return ""
    return "green" if proposed.green else "not green"


def checks_line(landing: Landing) -> str:
    """How many commands of the last run of the checks were red, or green."""
    outcomes = landing.checked.outcomes if landing.checked else ()
    bad = sum(1 for one in outcomes if not one.passed)
    if not outcomes:
        return ""
    return f"{bad} red" if bad else f"{len(outcomes)} green"


def build_line(record: Record) -> str:
    """The task of the plan: the one that runs, or the last once the build is behind."""
    progress = plan.progress(record)
    if progress is None:
        return ""
    at = progress.of if plan.done(record) else progress.at
    return f"task {at} of {progress.of}"


# The line of each phase after the build, from the landing.
LINES = MappingProxyType(
    {CHECKS: checks_line, REVIEW: review_line, PROPOSED: proposed_line}
)
