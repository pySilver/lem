"""`lem land propose`: the push of the tip and the pull request (`landing.md` E, "Push recorded
first").

The text is published first at a path of its own; the push carries a lease on Lem's last push
and is recorded before the forge's call; the forge's pull request is the one on the branch that
Lem pushed, else a new one. A run cut off anywhere finds what it did in git and on the forge.
"""

from functools import partial
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.landing import changes, frame, pr_text, step
from lem.kernel.errors import Refusal
from lem.model.landing import propose
from lem.records.journal.landing import NotGreen
from lem.records.landing.record import Pull

if TYPE_CHECKING:
    from pathlib import Path

    from lem.kernel.envelope import Envelope
    from lem.records.landing.propose import Proposed
    from lem.records.record import Record


def pushed(context: frame.Context, *, push: bool) -> Record:
    """Push the tip when origin lacks it, with the lease of Lem's last push, and record the
    push before any call to the forge."""
    record, world = context.record, context.world
    last = record.landing.pushed if record.landing else None
    if push:
        made = context.ports.git.push(context.worktree, world.branch, last)
        if not isinstance(made, str):
            raise Refusal(
                "git-refused",
                f"git refused the push of {world.branch}: {made.said}",
                "lem land next SLUG names what origin holds now",
            )
    return context.write(record, partial(changes.landing, pushed=world.tip))


def asked(context: frame.Context, number: int | None, words: tuple[str, str]) -> Pull:
    """A new pull request with `words` (its title and text), or the edit of `number`."""
    forge, world = context.ports.forge, context.world
    title, text = words
    if number is None:
        made = forge.open_pull(world.branch, world.rules.base, title, text)
    else:
        made = forge.update_pull(number, title, text)
    return Pull(number=made.number, url=made.url, title=made.title)


def pulled(
    context: frame.Context, proposal: propose.Proposal, words: tuple[str, str]
) -> Pull:
    """The forge's pull request with `words`: the one Lem pushed, edited when its words
    differ, else a new one."""
    found = proposal.adopt
    if found is not None and (found.title, found.body) == words:
        return Pull(number=found.number, url=found.url, title=found.title)
    return asked(context, found.number if found else None, words)


def opened(record: Record, *, made: Proposed, pull: Pull) -> Record:
    """The record with the proposal, the pull request and the phase `open`."""
    changed = changes.landing(record, proposed=made, pull=pull, phase="open")
    if made.reasons:
        entry = NotGreen(at=made.at, tip=made.tip, reasons=made.reasons)
        changed = changes.noted(changed, entry)
    return changes.moved(changed, "open", "the pull request is open", made.at)


def act(context: frame.Context, *, title: str, notes: str) -> Proposed:
    """Publish the text, push, open or adopt the pull request, and record the proposal."""
    proposal = propose.decide(context.record, context.world)
    if isinstance(proposal, Refusal):
        raise proposal
    text = pr_text.body(context.record, proposal.proposed.reasons, notes)
    made = replace(proposal.proposed, text=pr_text.published(context.folder, text))
    record = pushed(context, push=proposal.push)
    pull = pulled(context, proposal, (title, text))
    context.write(record, partial(opened, made=made, pull=pull))
    return made


def run(folder: Path, slug: str, *, title: str, notes: str) -> Envelope:
    """`lem land propose SLUG --title TITLE --notes FILE`."""
    return step.landed(folder, slug, "propose", partial(act, title=title, notes=notes))
