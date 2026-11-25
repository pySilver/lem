"""The line of a merge on a moved base in the pull request's text on the forge, once
(`landing.md` E, "Merge taken, text not updated"; `seam:pr-text-edit-fails`;
`main:land.noted`).

The new text is published at a path of its own and waits on record (`text_waits`) before the
forge's edit; the record keeps citing the text the forge confirmed until the edit succeeds. A
failed edit leaves the merge with its text not updated, and `merged` tries again.
"""

from functools import partial
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.landing import changes, merge_world
from lem.kernel import files
from lem.kernel.errors import Refusal
from lem.model.landing import merge_lines, reconcile
from lem.ports.faults import Unanswered
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.app.landing.frame import Context
    from lem.model.landing.world import PullSeen
    from lem.records.record import Record

TEXT = "pr-{0}-{1}.md"
SHORT = 12


def line_of(context: Context, landing: Landing) -> str | None:
    """The line the merge on record leaves in the pull request's text, by the trees of the
    checks' base and of the base it merged on."""
    merged = landing.merged
    if merged is None:
        return None
    tree = context.ports.git.tree(context.workspace.checkout, merged.parent)
    trees = reconcile.Trees(checks=merge_world.checks_tree(context), parent=tree)
    return reconcile.line_of(landing, merged, trees, context.world.rules.base)[0]


def confirmed(record: Record, *, text: str | None) -> Record:
    """The record with the merge's text updated, citing the text the forge confirmed."""
    landing = record.landing or Landing()
    proposed, merged = landing.proposed, landing.merged
    if proposed is not None and text is not None:
        proposed = replace(proposed, text=text, text_waits=None)
    if merged is not None:
        merged = replace(merged, text_updated=True)
    return changes.landing(record, proposed=proposed, merged=merged)


def waiting(record: Record, *, text: str) -> Record:
    """The record with a newer text of the pull request that waits for the forge."""
    proposed = (record.landing or Landing()).proposed
    if proposed is None:
        return record
    return changes.landing(record, proposed=replace(proposed, text_waits=text))


def named_of(record: Record, body: str) -> str:
    """The path of a body of the pull request's text in the task's folder: by its round and
    its digest, so a cut-off never changes a cited text."""
    digest = files.digest(body.encode())
    landing = record.landing or Landing()
    return TEXT.format(landing.round, digest[:SHORT])


def sent(context: Context, record: Record, edit: tuple[PullSeen, str]) -> Record:
    """Publish the newer text (`edit`: the pull request and its newer body), note that it
    waits, and send it to the forge; a failed edit is refused, and the step stays due."""
    pull, body = edit
    named, slug = named_of(record, body), record.task.slug
    files.publish(context.folder / named, body.encode())
    waits = context.write(record, partial(waiting, text=named))
    try:
        context.ports.forge.update_pull(pull.number, pull.title, body)
    except Unanswered as error:
        raise Refusal(
            "text",
            "GitHub merged the pull request, and the line of its merge did not reach its "
            f"text ({error.said}): the newer text waits",
            f"lem land merged {slug} tries the edit again",
        ) from error
    return context.write(waits, partial(confirmed, text=named))


def edited(context: Context, record: Record) -> Record:
    """Put the merge's line into the pull request's text on the forge, once, and mark the
    merge's text updated."""
    landing, pull = record.landing or Landing(), context.world.pull
    merged = landing.merged
    if merged is None or merged.text_updated:
        return record
    line = line_of(context, landing)
    if line is None or pull is None:
        return context.write(record, partial(confirmed, text=None))
    body = merge_lines.noted_body(pull.body, line)
    if body is None:
        return observed(context, record, pull.body)
    return sent(context, record, (pull, body))


def observed(context: Context, record: Record, body: str) -> Record:
    """The forge holds the line already (an edit that a stop cut off before its record):
    the body it shows is published by its digest and cited as the confirmed text, and the
    text that waited is cleared."""
    named = named_of(record, body)
    files.publish(context.folder / named, body.encode())
    return context.write(record, partial(confirmed, text=named))
