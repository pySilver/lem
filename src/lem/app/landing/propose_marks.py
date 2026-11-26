"""The pull request's lines of the findings Jev read (`main:land.jev_notes`, `jev_marked`):
each notes line and each item's title called under the bar ends with Jev's score, or why Jev
was not asked."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.landing import propose_jev
from lem.kernel.errors import Refusal
from lem.model.landing import propose_notes
from lem.model.landing.propose_jev import asked

if TYPE_CHECKING:
    from lem.app.landing.frame import Context
    from lem.model.landing.propose import Proposal
    from lem.model.landing.propose_facts import Facts, Filing
    from lem.model.landing.propose_jev import Said
    from lem.records.record import Record


def ending(said: Said) -> str:
    """The end of a finding's line: Jev's score, or why it was not asked."""
    if said.score is None:
        why = said.why or "no answer"
        return f"Jev: not asked ({why})"
    return f"Jev: {said.score:.2f}"


def ended(line: str, words: propose_jev.Words) -> str:
    """A line with Jev's word at its end, when Jev read it."""
    said = words.get(line.strip())
    return f"{line}; {ending(said)}" if said else line


def titled(filing: Filing, words: propose_jev.Words) -> Filing:
    """An item whose title ends with Jev's word, when Jev read it."""
    said = words.get(filing.path)
    if said is None:
        return filing
    named = filing.title or filing.path
    return replace(filing, title=f"{named}; {ending(said)}")


def marked(
    context: Context, proposal: Proposal, facts: Facts
) -> tuple[Proposal, Facts, Record]:
    """Read Jev's word on each finding under the bar, and end each of their lines with it."""
    words, record = propose_jev.read(
        context, asked(context.record, proposal.notes, facts)
    )
    proposal, facts = ended_notes(proposal, facts, words)
    return proposal, facts, record


def ended_notes(
    proposal: Proposal, facts: Facts, words: propose_jev.Words
) -> tuple[Proposal, Facts]:
    """End each line Jev read with its verdict."""
    lines = facts.notes.split("\n")
    notes = "\n".join(ended(line, words) for line in lines)
    parsed = propose_notes.parsed(notes)
    if isinstance(parsed, Refusal):
        raise parsed
    added = tuple(titled(filing, words) for filing in facts.added)
    return replace(proposal, notes=parsed), replace(facts, notes=notes, added=added)
