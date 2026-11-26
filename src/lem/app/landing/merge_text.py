"""The lines of a merge on a moved base and its agents in the pull request's text, once
(`landing.md` E, "Merge taken, text not updated"; `seam:pr-text-edit-fails`;
`main:land.noted`).

The new text is published at a path of its own and waits on record (`text_waits`) before the
forge's edit; the record keeps citing the text the forge confirmed until the edit succeeds. A
failed edit leaves the step due, and the step that needs the line tries again.
"""

from functools import partial
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.landing import changes, merge_notes
from lem.kernel import files
from lem.ports.faults import Unanswered
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.app.landing.frame import Context
    from lem.model.landing.world import PullSeen
    from lem.records.record import Record

TEXT = "pr-{0}-{1}.md"
SHORT = 12


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
    landing = record.landing or Landing()
    proposed, merged = landing.proposed, landing.merged
    if proposed is not None:
        proposed = replace(proposed, text_waits=text)
    if merged is not None:
        merged = replace(merged, text_updated=False)
    return changes.landing(record, proposed=proposed, merged=merged)


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
    named = named_of(record, body)
    files.publish(context.folder / named, body.encode())
    waits = context.write(record, partial(waiting, text=named))
    try:
        context.ports.forge.update_pull(pull.number, pull.title, body)
    except Unanswered as error:
        raise merge_notes.edit_refusal(record, error.said) from error
    return context.write(waits, partial(confirmed, text=named))


def edited(context: Context, record: Record) -> Record:
    """Confirm the lines of the merge agent and the moved base on the forge."""
    landing, pull = record.landing or Landing(), context.world.pull
    if pull is not None:
        body = merge_notes.body_of(
            pull.body, record, merge_notes.moved_line(context, landing)
        )
        if body is not None:
            return (
                observed(context, record, body)
                if body == pull.body
                else sent(context, record, (pull, body))
            )
    if landing.merged is not None and not landing.merged.text_updated:
        return context.write(record, partial(confirmed, text=None))
    return record


def observed(context: Context, record: Record, body: str) -> Record:
    """The forge holds the line already (an edit that a stop cut off before its record):
    the body it shows is published by its digest and cited as the confirmed text, and the
    text that waited is cleared."""
    named = named_of(record, body)
    proposed = record.landing.proposed if record.landing else None
    merged = record.landing.merged if record.landing else None
    if (
        merged is None
        and proposed
        and proposed.text == named
        and proposed.text_waits is None
    ):
        return record
    files.publish(context.folder / named, body.encode())
    return context.write(record, partial(confirmed, text=named))
