"""`lem land read`: the brief of the review that is due, or the record of the review an agent
ran.

With no file the step publishes the brief (`app/landing/review_brief.py`), starts the review's
span, and names next the command that takes the agent's record. With `--record FILE` it reads
the agent's JSON, in the form `prompts/review.md` gives (`model.landing.review_said.Said`), and
records it for the attempt and the tip now, or refuses it with what is wrong.
"""

from functools import partial
from typing import TYPE_CHECKING

import msgspec

from lem.app.landing import (
    review_brief,
    review_changes,
    review_facts,
    review_files,
    review_settings,
    step,
)
from lem.kernel.envelope import Envelope, Next
from lem.kernel.errors import Refusal
from lem.model.landing import review, review_due
from lem.records.base import Frozen

if TYPE_CHECKING:
    from pathlib import Path

    from lem.app.landing import frame
    from lem.records.landing.review import Reviewed


class Briefed(Frozen, frozen=True, kw_only=True):
    """The brief, published: the attempt and the tip the record names, the floor, the brief's
    path in the task's folder, where the record goes, and the brief itself."""

    attempt: int
    tip: str
    floor: review_due.Floor
    path: str
    record: str
    brief: review_brief.Brief


def known(context: frame.Context) -> tuple[review_facts.Gathered, review_due.Facts]:
    """The facts of the change, and what a review's record is checked against."""
    found = review_facts.gathered(context)
    return found, review_facts.facts(context, found)


def briefed(context: frame.Context) -> Briefed:
    """Publish the brief of the review that is due, and start its span."""
    found, facts = known(context)
    topics = review_settings.read(context.workspace.checkout).flow.topics
    brief = review_brief.made(context, found, facts, topics)
    context.write(
        context.record,
        partial(review_changes.started, attempt=brief.attempt, now=context.world.now),
    )
    return Briefed(
        attempt=brief.attempt,
        tip=brief.tip,
        floor=brief.floor,
        path=review_brief.published(context, brief),
        record=brief.record,
        brief=brief,
    )


def taken(context: frame.Context, *, path: str) -> Reviewed:
    """Record the review of the file at `path`, or refuse it."""
    read = review_files.said(review_files.task_file(path, context.folder))
    _, facts = known(context)
    attempt = review.decide(context.record, context.world, read, facts)
    if isinstance(attempt, Refusal):
        raise attempt
    context.write(
        context.record, partial(review_changes.recorded, review=attempt, said=read)
    )
    return attempt


def answering(slug: str, envelope: Envelope) -> Envelope:
    """The envelope of a brief, whose next is the command that takes the agent's record."""
    found = msgspec.json.decode(envelope.outcome or b"null", type=Briefed)
    attempt = found.attempt
    following = Next(
        act="spawn",
        job="review",
        command=f"lem land read {slug} --record FILE",
        paths=(found.path,),
        why=(
            f"a review agent reads the change as prompts/review.md says, with the brief "
            f"{found.path}, and writes FILE, {found.record} in the task's folder: the record "
            f"of attempt {attempt}, which this command takes"
        ),
    )
    return msgspec.structs.replace(envelope, following=following)


def run(folder: Path, slug: str, path: str | None) -> Envelope:
    """`lem land read SLUG [--record FILE]`."""
    if path is None:
        return answering(slug, step.landed(folder, slug, "read", briefed))
    return step.landed(folder, slug, "read", partial(taken, path=path))
