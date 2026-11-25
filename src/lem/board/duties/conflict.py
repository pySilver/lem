"""A duty of the board server: the wakes a pull request owes its task's session (`wake …
merged`, `wake … conflict` and `wake … refused` of `serve.duties` on `main`).

- `merged`: the merge ended the task (`landed`, or `dropped` because its pull request was closed
  on the forge), its worktree is still there, and no session of it was woken or opened since it
  ended: one wake, so that its session cleans up; with no live session the wake opens one.
- `conflict`: the forge's last look calls the pull request conflicting at the head Lem proposed
  last, and no session was woken or opened for a conflict since that proposal: one wake for each
  head. After another task's merge, an open task with no conflict waits as it is (the owner's
  ruling "After a merge, Lem repairs only a pull request with a conflict").
- `refused`: a merge of the tip Lem proposed last was refused, the merge agent's, or the owner's
  because the base moved (Lem's refusal of kind `base`), and no session was woken or opened
  since the refusal.

A task two releases back gets no wake but the one after its merge: its pull request is still
watched, and its session waits for the owner's drop or resume.
"""

from typing import TYPE_CHECKING

from lem.app.landing.merged import CLOSED
from lem.app.owner import forge
from lem.board.duties import wakes
from lem.records.holds import ReleaseHold
from lem.store import tasks
from lem.store.retention.fold import last_state_of, past_of

if TYPE_CHECKING:
    from lem.board.duties.context import Duty
    from lem.records.record import Record


def tick(duty: Duty) -> None:
    """Wake each task whose pull request owes its session a wake."""
    look = forge.read(duty.state)
    for record in tasks.every(duty.state):
        if ended(record):
            cleaned(duty, record)
        elif watched(record) and not conflicted(duty, record, look):
            refused(duty, record)


def watched(record: Record) -> bool:
    """Whether the task is open and its session may be woken: not two releases back."""
    task = record.task
    return task.status == "open" and not isinstance(task.hold, ReleaseHold)


def ended(record: Record) -> bool:
    """Whether the merge ended the task: it landed, or the forge closed its pull request."""
    status = record.task.status
    if status == "landed":
        return True
    last = last_state_of(past_of(record), record.journal)
    line = (last.line or "") if last else ""
    return status == "dropped" and line.startswith(CLOSED)


def cleaned(duty: Duty, record: Record) -> None:
    """Wake the ended task once while its worktree stays, so that its session cleans up."""
    slug = record.task.slug
    if duty.here.worktree(slug) is None:
        return
    if not wakes.after_end(duty, slug, record.task.since):
        wakes.woken(duty, slug, "merged", not_before=record.task.since)


def conflicted(duty: Duty, record: Record, look: forge.Look) -> bool:
    """Wake the task for a conflict at the proposed head, once for that proposal; whether the
    forge calls it conflicting there."""
    landing = record.landing
    proposed = landing.proposed if landing else None
    if proposed is None or not forge.conflicts(look, record):
        return False
    slug = record.task.slug
    if not wakes.since(duty, slug, proposed.at, ("conflict",)):
        wakes.woken(duty, slug, "conflict", proposed.tip)
    return True


def refused(duty: Duty, record: Record) -> None:
    """Wake the task once after a refused merge of the proposed tip that its session answers."""
    landing = record.landing
    refusal = landing.refused if landing else None
    if refusal is None or not answered_by_session(record):
        return
    slug = record.task.slug
    if not wakes.since(duty, slug, refusal.at):
        wakes.woken(duty, slug, "refused")


def answered_by_session(record: Record) -> bool:
    """Whether the refusal on record is of the tip Lem proposed last, and the merge agent's,
    or Lem's refusal of the owner's merge because the base moved."""
    landing = record.landing
    refusal = landing.refused if landing else None
    proposed = landing.proposed if landing else None
    if refusal is None or proposed is None or refusal.tip != proposed.tip:
        return False
    moved = refusal.source == "lem" and refusal.kind == "base"
    return refusal.by == "merger" or moved
