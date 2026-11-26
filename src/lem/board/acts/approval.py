"""Whether the owner's approval of a merge may go, before its merge runs: from its confirm step,
on an open task, for the tip proposed now; and its note, which says it was refused, that his
approval stands, or that its merge runs (`serve.act_merge` on `main`).
"""

from typing import TYPE_CHECKING

from lem.app.owner import forge
from lem.app.tasks import release
from lem.board import merge_look
from lem.board.acts import merge_status, merging
from lem.board.acts.asked import refused
from lem.board.acts.notes import Note
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from lem.board.acts.asked import Asked
    from lem.records.record import Record

ACT = "merge"
CONFIRM = "yes"


def require_open(record: Record) -> None:
    """Refuse an approval while the task is parked or its pull request is not open."""
    task = record.task
    parked = merge_look.parked_reason(record)
    if parked is not None:
        raise Refusal("parked", parked, f"resume it with /lem resume {task.slug}")
    if task.status != "open":
        why = f"{task.slug} is not open for a merge now: it is {task.status}."
        raise Refusal("not-open", why, "read the task's page again")


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
    require_open(record)
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
    if merge_status.standing(record) is not None:
        return Note(
            task=asked.slug, act=ACT, state="stands", said=merging.stands(record)
        )
    if forge.conflicts(forge.read(asked.state), record):
        why = (
            "GitHub reports a conflicting pull request. "
            "The task’s session brings it onto the base first."
        )
        return Note(task=asked.slug, act=ACT, state="refused", said=why)
    what = merging.what_of(record)
    said = (
        f"Lem merges {what} on your approval. The page shows the result when it ends."
    )
    return Note(task=asked.slug, act=ACT, state="running", said=said)
