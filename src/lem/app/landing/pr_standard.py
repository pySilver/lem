"""The standard track's part of the pull request's text after the request
(`main:land.pr_text`): the criteria and their changes, the checks from each command to the
careful call, the decisions of the build with each important story folded, and the notes with
what was seen outside the change."""

from typing import TYPE_CHECKING

from lem.app.landing import (
    pr_checks,
    pr_closing,
    pr_criteria,
    pr_decisions,
    pr_notes,
    pr_read,
    pr_reviews,
    pr_tests,
)
from lem.app.landing.pr_inputs import Block, Lines, block
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.model.landing.propose import Proposal
    from lem.model.landing.propose_facts import Facts
    from lem.records.record import Record


def first(record: Record) -> Lines:
    """The checks before the bar: each command, the criteria's tests, the polish pass, the
    personas' read and what changed after it, the scout, and the cause."""
    landing = record.landing or Landing()
    tests = (pr_tests.criteria_line(record), pr_tests.polish_line(landing))
    read = (pr_read.read_line(record), *pr_read.unread(record))
    read += pr_read.scout(record)
    cause = pr_checks.cause(record, before=True)
    return (*pr_checks.commands(landing.checked), *tests, *read, *cause)


def checks(record: Record, proposal: Proposal, facts: Facts) -> Lines:
    """The checks of the standard track, from each command to the careful call."""
    landing = record.landing or Landing()
    measured = (
        *pr_checks.lowered_lines(landing.checked, full=True),
        pr_checks.size(landing.checked),
    )
    fixed = pr_notes.fixed(proposal.notes)
    reviews = pr_reviews.lines(landing, fixed, full=True)
    closing = pr_closing.lines(record, facts, proposal.careful, full=True)
    return (*first(record), *measured, *reviews, *closing)


def blocks(record: Record, proposal: Proposal, facts: Facts) -> tuple[Block, ...]:
    """The blocks of the standard track after the request."""
    decided = pr_decisions.lines(record) or ("none",)
    stories = pr_decisions.stories(record)
    notes = pr_notes.standard(record, proposal.notes, facts)
    return (
        *pr_criteria.full(record),
        Block(heading="## Checks", lines=checks(record, proposal, facts)),
        Block(heading="## Decisions of the build", lines=(*decided, *stories)),
        *block(None, notes),
    )
