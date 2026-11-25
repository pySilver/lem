"""The lines of the sections of a task's map from its landing on, when they hold no document:
the checks, the review and the pull request (`board_task.empty_reason` on `main`)."""

from typing import TYPE_CHECKING

from lem.board.views.artifacts.before import either
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.records.record import Record

NO_LANDING = Landing()


def checks(record: Record) -> str:
    """The checks' section."""
    checked = (record.landing or NO_LANDING).checked
    shown = "no output kept: Checks and review shows the results"
    return either(
        record,
        shown if checked and checked.outcomes else None,
        "not yet: the checks run when the branch’s turn to land comes",
    )


def review(record: Record) -> str:
    """The review's section."""
    reviews = (record.landing or NO_LANDING).reviews
    shown = "no document: Checks and review shows each round" if reviews else None
    return either(record, shown, "not yet: the review comes after the checks")


def proposal(record: Record) -> str:
    """The pull request's section."""
    proposed = (record.landing or NO_LANDING).proposed
    shown = "no document: the proposal is on Checks and review" if proposed else None
    return either(record, shown, "not yet: the proposal writes it")


def pending(record: Record) -> str:
    """What the map says while an edit to the pull request text waits for the forge."""
    proposed = (record.landing or NO_LANDING).proposed
    return (
        ". A newer text waits for GitHub." if proposed and proposed.text_waits else ""
    )
