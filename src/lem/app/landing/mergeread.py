"""`lem land merge-review`: the merge agent's brief, or its reply written down.

With no reply the step publishes the brief at a path named by the tip and the base it reads, and
says the command that writes the reply down with them. The brief names the standing text the
merge agent follows and the facts of the task (`merge_brief.py`). A reply, or `--no-answer`, of
the brief of the proposed tip becomes the read of that tip on the brief's base: a verdict, or an
answer that could not be recorded, the first of which a fresh merge agent answers again
(`model/landing/mergeread.py`).
"""

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from lem.app.landing import changes, following, merge_brief, merge_step, merge_world
from lem.kernel import files
from lem.kernel.errors import Refusal
from lem.model.landing import merge_asked, mergeread
from lem.records.journal.merge import ReadNoted

if TYPE_CHECKING:
    from lem.app.landing.frame import Context
    from lem.kernel.envelope import Envelope, Next
    from lem.records.landing.propose import MergeRead
    from lem.records.record import Record

WHOLE = merge_asked.WHOLE
# The reply of the read that settles, as the owner reads it beside the read: agent prose,
# written whole, never cited; for an agent that gave none, the reason in its place.
REVIEW = "merge-review.md"
# The tip and the base of the brief a reply answers, as the step printed them.
type Answered = tuple[str, str] | None


def briefed(context: Context, brief: Answered) -> mergeread.Briefed:
    """The brief a reply answers, by its tip and base, which the step wrote; refused when
    they are not given, not whole commits, or name no brief it wrote."""
    tip, base = brief or ("", "")
    written = merge_brief.path_of(context, tip, base)
    if not (WHOLE.fullmatch(tip) and WHOLE.fullmatch(base) and written.is_file()):
        raise Refusal(
            "brief-of",
            f"no brief of the tip {tip!r} on the base {base!r} was written: a reply is "
            "written down with the tip and the base of the brief it answers",
            "give --tip and --base as lem land merge-review printed them with the brief",
        )
    tree = context.ports.git.tree(context.workspace.checkout, base)
    moved = tree != merge_world.checks_tree(context)
    return mergeread.Briefed(tip=tip, base=base, base_tree=tree, moved=moved)


def said(reply: str | None) -> str | None:
    """The reply's words, or None for an agent that ended with no answer."""
    if reply is None:
        return None
    try:
        return Path(reply).read_text(encoding="utf-8")
    except OSError as error:
        raise Refusal(
            "reply",
            f"{reply} cannot be read ({error.strerror})",
            "--file names the merge agent's reply",
        ) from error


def noted(record: Record, *, read: MergeRead) -> Record:
    """The record with the read and its note in the journal; a read that settles with a
    verdict answers Lem's refusal of this tip for a moved base."""
    landing = record.landing
    before = landing.reads if landing else ()
    refused = landing.refused if landing else None
    answers = (
        read.verdict is not None
        and refused is not None
        and (refused.source, refused.kind, refused.tip) == ("lem", "base", read.tip)
    )
    changed = changes.landing(
        record, reads=(*before, read), refused=None if answers else refused
    )
    return changes.noted(changed, ReadNoted(at=read.at, read=read))


def act(
    context: Context, *, reply: str | None, brief: Answered, no_answer: bool
) -> merge_brief.Brief | MergeRead:
    """Publish the brief, or record the reply (or the lack of one) to the brief of `brief`."""
    if reply is None and not no_answer:
        return merge_brief.published(context)
    text = said(reply)
    read = mergeread.decide(
        context.record, briefed(context, brief), text, context.world.now
    )
    if isinstance(read, Refusal):
        raise read
    context.write(context.record, partial(noted, read=read))
    again = mergeread.again(read)
    if again is not None:
        raise again
    shown = f"No answer of the merge agent: {read.why}.\n" if text is None else text
    files.write_whole(context.folder / REVIEW, shown.encode())
    return read


def told(slug: str, outcome: object) -> Next | None:
    """After a brief: the command that writes the reply down, with its tip and base."""
    if not isinstance(outcome, merge_brief.Brief):
        return None
    return following.answered(slug, outcome.brief, (outcome.tip, outcome.base))


def run(
    folder: Path,
    slug: str,
    reply: str | None,
    brief: Answered,
    *,
    no_answer: bool = False,
) -> Envelope:
    """`lem land merge-review SLUG [--file FILE|--no-answer --tip TIP --base BASE]`."""
    given = partial(act, reply=reply, brief=brief, no_answer=no_answer)
    return merge_step.landed(
        folder, slug, mergeread.STEP, given, merge_step.Hooks(told=partial(told, slug))
    )
