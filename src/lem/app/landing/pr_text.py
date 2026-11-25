"""The pull request's text, in the order the owner reads it (`main:land.pr_text`,
`small_text`): green or each reason it is not, then the request in the owner's words, the
criteria with their tests, each check with what it returned, each decision of the record with
who took it and why, and the agent's notes with what was seen outside the change.

The text is a function of the record, the facts of the branch and the notes, so a proposal cut
off and made again writes the same bytes. Each body is published at a path of its own,
`pr-ROUND-DIGEST.md`, which the record cites. The template only prints its blocks.
"""

from typing import TYPE_CHECKING

import jinja2

from lem.app.landing import (
    pr_checks,
    pr_closing,
    pr_criteria,
    pr_decisions,
    pr_fast,
    pr_head,
    pr_notes,
    pr_read,
    pr_reviews,
)
from lem.app.landing.pr_inputs import Block, Lines, Text, block
from lem.kernel import files
from lem.model.landing.propose_facts import small
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from pathlib import Path

    from lem.model.landing.propose import Proposal
    from lem.model.landing.propose_facts import Facts
    from lem.records.record import Record

SHORT = 12
TEMPLATES = jinja2.Environment(
    loader=jinja2.PackageLoader("lem.app.landing", "templates"),
    autoescape=jinja2.select_autoescape(default=False, default_for_string=False),
    undefined=jinja2.StrictUndefined,
    keep_trailing_newline=True,
)


def checks(record: Record, proposal: Proposal, facts: Facts) -> Lines:
    """The checks of the standard track: each command, the criteria's tests, the polish
    pass, the personas' read, the cause, the bar, the size, each review, the plan talk,
    each stand-in and the careful call."""
    landing = record.landing or Landing()
    checked = landing.checked
    head = (
        *pr_checks.commands(checked),
        pr_checks.criteria_line(record),
        pr_checks.polish_line(landing),
        pr_read.read_line(record),
        *pr_read.unread(record),
        *pr_read.scout(record),
        *pr_checks.cause(record, before=True),
    )
    measured = (*pr_checks.bar(checked, full=True), pr_checks.size(checked))
    reviews = pr_reviews.lines(landing, pr_notes.fixed(proposal.notes), full=True)
    closing = pr_closing.lines(record, facts, proposal.careful, full=True)
    return (*head, *measured, *reviews, *closing)


def standard(record: Record, proposal: Proposal, facts: Facts) -> tuple[Block, ...]:
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


def fast(record: Record, proposal: Proposal, facts: Facts) -> tuple[Block, ...]:
    """The blocks of the fast track after the request: its criterion, its checks, its
    decisions when it has any, and the notes."""
    landing = record.landing or Landing()
    checked = landing.checked
    reviews = pr_reviews.lines(landing, pr_notes.fixed(proposal.notes), full=False)
    lines = (
        *pr_checks.commands(checked),
        *pr_checks.cause(record, before=False),
        *pr_checks.bar(checked, full=False),
        *reviews,
        *pr_closing.lines(record, facts, proposal.careful, full=False),
    )
    return (
        *pr_fast.criterion(record),
        Block(heading="## Checks", lines=lines),
        *block("## Decisions", pr_decisions.lines(record)),
        *pr_notes.tail(record, proposal.notes, facts),
    )


def body(record: Record, proposal: Proposal, facts: Facts) -> str:
    """The whole text of the pull request."""
    track = fast if small(record) else standard
    head = pr_head.blocks(record, proposal)
    blocks = (*head, *pr_criteria.request(record), *track(record, proposal, facts))
    return TEMPLATES.get_template("pr.md.j2").render(text=Text(blocks=blocks))


def published(folder: Path, number: int, text: str) -> str:
    """Publish the text in the task's folder `folder` at a path named by the round and its
    digest, and give that path."""
    encoded = text.encode()
    short = files.digest(encoded)[:SHORT]
    named = f"pr-{number}-{short}.md"
    files.publish(folder / named, encoded)
    return named
