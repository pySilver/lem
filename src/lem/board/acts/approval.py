"""Whether the owner's approval of a merge may go, before its merge runs: from its confirm step,
on an open task, for the tip proposed now; and its note, which says it was refused, that his
approval stands, or that its merge runs (`serve.act_merge` on `main`).
"""

from typing import TYPE_CHECKING

from lem.app.tasks import release
from lem.board.acts import merging
from lem.board.acts.asked import refused
from lem.board.acts.notes import Note
from lem.kernel.errors import Refusal
from lem.model.landing import merge_standing

if TYPE_CHECKING:
    from lem.board.acts.asked import Asked
    from lem.records.record import Record

ACT = "merge"
CONFIRM = "yes"


def checked(asked: Asked) -> Record:
    """The task's record when the approval may go: from the confirm step, on an open task,
    for the tip proposed now."""
    if asked.given.confirm != CONFIRM:
        why = (
            "A merge runs only from its confirm step, which names the pull request and "
            "the commit: nothing was merged."
        )
        raise Refusal("confirm", why, "approve it on its confirm step")
    record = release.checked(asked.state, asked.slug)
    task = record.task
    if task.status != "open":
        why = f"{task.slug} is not open for a merge now: it is {task.status}."
        raise Refusal("not-open", why, "read the task's page again")
    proposed = record.landing.proposed if record.landing else None
    if proposed is None or asked.given.tip != proposed.tip:
        why = (
            "The branch was proposed again since the confirm step showed it: nothing was "
            "merged."
        )
        raise Refusal("tip", why, "read the confirm step again")
    return record


def note_of(asked: Asked) -> Note:
    """The note of the approval before its merge runs: refused, standing, or running."""
    try:
        record = checked(asked)
    except Refusal as refusal:
        return refused(ACT, asked.slug, refusal)
    if merge_standing.standing_of(record) is not None:
        return Note(
            task=asked.slug, act=ACT, state="stands", said=merging.stands(record)
        )
    what = merging.what_of(record)
    said = (
        f"Lem merges {what} on your approval. The page shows the result when it ends."
    )
    return Note(task=asked.slug, act=ACT, state="running", said=said)
