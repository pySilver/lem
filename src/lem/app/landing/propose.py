"""`lem land propose`: the pull request's text, the push of the tip and the pull request
(`landing.md` C, row 7; E, "Push recorded first"; `stages/land.md` step 6).

The gates come first, each a refusal before anything is written or pushed; then the text is
published at a path of its own, the push carries a lease on Lem's last push and is recorded
before the forge's call, and the forge's pull request is the task's own, edited, or a new one.
A run cut off anywhere finds what it did in git and on the forge.
"""

from functools import partial
from typing import TYPE_CHECKING

import msgspec
from msgspec.structs import replace

from lem.app.landing import changes, frame, pr_text, propose_push, propose_seen, step
from lem.kernel.errors import Refusal
from lem.model.landing import propose
from lem.records.base import Frozen
from lem.records.journal.landing import NotGreen
from lem.records.landing.record import Landing, Pull

if TYPE_CHECKING:
    from pathlib import Path

    from lem.kernel.envelope import Envelope
    from lem.records.landing.propose import Proposed
    from lem.records.record import Record


class Made(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """What `propose` gives: the pull request's number and address, green or each reason it
    is not, whether it is careful, who merges it, the tip and the branch, and the text's
    path in the task's folder."""

    task: str
    pull: Pull
    green: bool
    reasons: tuple[str, ...]
    careful: bool
    who_acts: str
    tip: str
    branch: str
    text: str


def opened(record: Record, *, made: Proposed, pull: Pull) -> Record:
    """The record with the proposal, the pull request and the phase `open`; a request that
    is not green names its reasons in the journal."""
    changed = changes.landing(record, proposed=made, pull=pull, phase="open")
    if made.reasons:
        entry = NotGreen(at=made.at, tip=made.tip, reasons=made.reasons)
        changed = changes.noted(changed, entry)
    return changes.moved(changed, "open", f"pull request {pull.url}", made.at)


def act(context: frame.Context, *, title: str, notes: str) -> Made:
    """Gate, publish the text, push, open, adopt or edit the pull request, and record the
    proposal."""
    facts = propose_seen.gathered(context, notes)
    proposal = propose.decide(context.record, context.world, facts, title)
    if isinstance(proposal, Refusal):
        raise proposal
    text = pr_text.body(context.record, proposal, facts)
    round_ = (context.record.landing or Landing()).round
    made = replace(
        proposal.proposed, text=pr_text.published(context.folder, round_, text)
    )
    record = propose_push.pushed(context, push=proposal.push)
    pull = propose_push.pulled(context, proposal, (title, text))
    context.write(record, partial(opened, made=made, pull=pull))
    return Made(
        task=record.task.slug,
        pull=pull,
        green=made.green,
        reasons=made.reasons,
        careful=made.careful,
        who_acts=made.who_acts,
        tip=made.tip,
        branch=context.world.branch,
        text=made.text or "",
    )


def said(made: Made) -> str:
    """The line for the owner: the pull request's address, and green or each reason."""
    if made.green:
        return f"pull request {made.pull.url}: green"
    return f"pull request {made.pull.url}: not green: {'; '.join(made.reasons)}"


def run(folder: Path, slug: str, *, title: str, notes: str) -> Envelope:
    """`lem land propose SLUG --title TITLE --notes FILE`."""
    envelope = step.landed(
        folder, slug, "propose", partial(act, title=title, notes=notes)
    )
    raw = envelope.outcome
    made = msgspec.json.decode(raw, type=Made) if raw is not None else None
    return replace(envelope, say=said(made)) if made else envelope
