"""`lem land merge-review`: the merge agent's brief, or its reply written down.

With no reply the step publishes the brief (the pull request's text and what to answer) at a
path named by the tip and the base, and prints it with them; the agent's reply, with the tip and
the base the step printed, becomes the read. An agent that ends with no answer, and a read that
carries over a moved base, are the step `land-merge`'s.
"""

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from lem.app.landing import changes, frame, step
from lem.kernel import files
from lem.kernel.errors import Refusal
from lem.model.landing import mergeread
from lem.records.base import Frozen, Sha
from lem.records.journal.merge import ReadNoted

if TYPE_CHECKING:
    from lem.kernel.envelope import Envelope
    from lem.records.landing.propose import MergeRead, Proposed
    from lem.records.record import Record

ASK = (
    "Read the pull request below for its merge into the base. Answer on the first line "
    "`merge` when it may merge as it is, or `call` when the owner must read it, then why."
)
SHORT = 12
BRIEF = "merge-brief-{0}-{1}.md"
# The tip and the base of the brief a reply answers, as the step printed them.
type Answered = tuple[str, str] | None


class Brief(Frozen, frozen=True, kw_only=True):
    """The brief the merge agent reads: its path, and the tip and base it is of."""

    brief: str
    tip: Sha
    base: Sha


def briefed(context: frame.Context) -> Brief:
    """Publish the brief of the proposed tip on origin's base now."""
    proposed = mergeread.brief_refusal(context.record)
    if isinstance(proposed, Refusal):
        raise proposed
    base, tip = context.world.base, proposed.tip
    named = BRIEF.format(tip[:SHORT], base[:SHORT])
    path = context.folder / named
    files.publish(path, text_of(context, proposed))
    return Brief(brief=str(path), tip=tip, base=base)


def text_of(context: frame.Context, proposed: Proposed) -> bytes:
    """The brief: what the agent answers, then the pull request's text the proposal cites."""
    path = context.folder / (proposed.text or "")
    said = path.read_text(encoding="utf-8")
    return f"{ASK}\n\n{said}".encode()


def noted(record: Record, *, read: MergeRead) -> Record:
    """The record with the read, and its note in the journal."""
    before = record.landing.reads if record.landing else ()
    changed = changes.landing(record, reads=(*before, read))
    entry = ReadNoted(at=read.at, read=read)
    return changes.noted(changed, entry)


def act(
    context: frame.Context, *, reply: str | None, brief: Answered
) -> Brief | MergeRead:
    """Publish the brief, or record the reply to the brief of `brief` (its tip and base)."""
    if reply is None:
        return briefed(context)
    if brief is None:
        raise Refusal(
            "brief-of",
            "a reply is recorded with the tip and the base of the brief it answers",
            "give --tip and --base as lem land merge-review printed them",
        )
    said = Path(reply).read_text(encoding="utf-8")
    read = mergeread.decide(context.record, context.world, said, brief)
    if isinstance(read, Refusal):
        raise read
    context.write(context.record, partial(noted, read=read))
    return read


def run(folder: Path, slug: str, reply: str | None, brief: Answered) -> Envelope:
    """`lem land merge-review SLUG [--file FILE --tip TIP --base BASE]`."""
    given = partial(act, reply=reply, brief=brief)
    return step.landed(folder, slug, mergeread.STEP, given)
