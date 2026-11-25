"""The reviewer's item leaves after the forge merges and before the task lands."""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.store import reviewer_items

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record
    from lem.store.places import Workspace


def removed(workspace: Workspace, record: Record) -> None:
    """Remove the task's own reviewer item, with a retry when its removal fails."""
    path = reviewer_items.relative(workspace.checkout, record.task.backlog_item or "")
    if path is None:
        return
    try:
        reviewer_items.remove(workspace.state, path)
    except OSError as error:
        entry = reviewer_items.file_of(workspace.state, path)
        raise refused(record, entry, error) from error


def refused(record: Record, entry: Path, error: OSError) -> Refusal:
    """The owner gets the failed item's path and the command that tries again."""
    pull = record.landing.pull if record.landing else None
    address = pull.url if pull else "the pull request"
    why = error.strerror or error
    slug = record.task.slug
    return Refusal(
        "item-remove",
        f"GitHub merged {address}, and the file of the backlog item the task was "
        f"started from, {entry}, was not removed ({why}). The task stays open",
        f"lem land merged {slug} tries the removal again",
    )
