"""`lem land propose`: the pull request's text, the push of the tip and the pull request
(`landing.md` C, row 7; E, "Push recorded first"; `stages/land.md` step 6).

The gates come first, each a refusal before anything is written or pushed, then Jev's one read
of each finding called under the bar, which may stop the step once; then the text is
published at a path of its own, the push carries a lease on Lem's last push and is recorded
before the forge's call, and the forge's pull request is the task's own, edited, or a new one.
A run cut off anywhere finds what it did in git and on the forge.
"""

from functools import partial
from typing import TYPE_CHECKING

import msgspec
from msgspec.structs import replace

from lem.app.landing import (
    pr_text,
    propose_made,
    propose_marks,
    propose_push,
    propose_seen,
    step,
)
from lem.kernel.errors import Refusal
from lem.model.landing import propose

if TYPE_CHECKING:
    from pathlib import Path

    from lem.app.landing.frame import Context
    from lem.kernel.envelope import Envelope


def written(context: Context, title: str, notes: str) -> tuple[propose.Proposal, str]:
    """The proposal and the pull request's text, or the refusal of the first gate the
    request does not pass, before anything is written or pushed."""
    facts = propose_seen.gathered(context, notes)
    proposal = propose.decide(context.record, context.world, facts, title)
    if isinstance(proposal, Refusal):
        raise proposal
    proposal, facts = propose_marks.marked(context, proposal, facts)
    return proposal, pr_text.body(context.record, proposal, facts)


def published(context: Context, text: str) -> str:
    """Publish the text in the task's folder under its round, and give its path."""
    landing = context.record.landing
    return pr_text.published(context.folder, landing.round if landing else 1, text)


def act(context: Context, *, title: str, notes: str) -> propose_made.Made:
    """Gate, publish the text, push, open, adopt or edit the pull request, and record the
    proposal."""
    proposal, text = written(context, title, notes)
    made = replace(proposal.proposed, text=published(context, text))
    record = propose_push.pushed(context, push=proposal.push)
    pull = propose_push.pulled(context, proposal, (title, text))
    record = context.write(record, partial(propose_made.opened, made=made, pull=pull))
    return propose_made.given(record, made, (pull, context.world.branch))


def run(folder: Path, slug: str, *, title: str, notes: str) -> Envelope:
    """`lem land propose SLUG --title TITLE --notes FILE`."""
    proposal = partial(act, title=title, notes=notes)
    envelope = step.landed(folder, slug, "propose", proposal)
    if envelope.outcome is None:
        return envelope
    made = msgspec.json.decode(envelope.outcome, type=propose_made.Made)
    return replace(envelope, say=propose_made.said(made))
