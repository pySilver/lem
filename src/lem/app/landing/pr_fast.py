"""The fast track's criterion in the pull request's text (`main:land.small_text`): the track
and why, who approved it when it was not the owner, the criterion with what its tests gave, and
each change of it during the build."""

from typing import TYPE_CHECKING

from lem.app.landing import (
    pr_bar,
    pr_checks,
    pr_closing,
    pr_decisions,
    pr_notes,
    pr_reviews,
)
from lem.app.landing.pr_changes import change_line
from lem.app.landing.pr_criteria import NO_REASON, criterion_lines
from lem.app.landing.pr_inputs import Block, Lines, block
from lem.model.landing.green_words import reason
from lem.records.decisions import CriterionChanged
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.model.landing.propose import Proposal
    from lem.model.landing.propose_facts import Facts
    from lem.records.record import Record

UNREAD = "the personas did not read it."


def approved_by(record: Record) -> str:
    """Who approved the criterion when it was not the owner, and that no persona read it."""
    approvals = record.task.criteria.approvals
    newest = approvals[-1] if approvals else None
    if newest is None or newest.by not in {"lem", "alone"}:
        return ""
    day = newest.at.date().isoformat()
    if newest.by == "lem":
        return f" Lem approved it in the owner's name on {day}; {UNREAD}"
    opened = (
        "the night opened the task"
        if record.task.night
        else "someone else wrote the request"
    )
    return f" Lem approved it on {day} without the owner ({opened}); {UNREAD}"


def criterion(record: Record) -> tuple[Block, ...]:
    """The fast track's criterion block."""
    task = record.task
    why = reason(task.criteria.why or NO_REASON)
    found = tuple(
        line for one in task.criteria.criteria for line in criterion_lines(record, one)
    )
    changes = tuple(
        change_line(record, change)
        for change in task.decisions
        if isinstance(change, CriterionChanged)
    )
    track = f"The fast track, because {why}.{approved_by(record)}"
    return (
        Block(
            heading="## The acceptance criterion", lines=(track, "", *found, *changes)
        ),
    )


def checks(record: Record, proposal: Proposal, facts: Facts) -> Lines:
    """The fast track's checks: each command, the cause, the bar, each review, each
    stand-in and the careful call."""
    landing = record.landing or Landing()
    reviews = pr_reviews.lines(landing, pr_notes.fixed(proposal.notes), full=False)
    closing = pr_closing.lines(record, facts, proposal.careful, full=False)
    measured = (
        *pr_checks.lowered_lines(landing.checked, full=False),
        *pr_bar.lines(facts.bar_read, full=False),
    )
    return (
        *pr_checks.commands(landing.checked),
        *pr_checks.cause(record, before=False),
        *measured,
        *reviews,
        *closing,
    )


def blocks(record: Record, proposal: Proposal, facts: Facts) -> tuple[Block, ...]:
    """The blocks of the fast track after the request: its criterion, its checks, its
    decisions when it has any, and the notes."""
    return (
        *criterion(record),
        Block(heading="## Checks", lines=checks(record, proposal, facts)),
        *block("## Decisions", pr_decisions.lines(record)),
        *pr_notes.tail(record, proposal.notes, facts),
    )
