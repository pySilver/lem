"""Attach the task's plan and add the workspace's board link."""

from typing import TYPE_CHECKING

from lem.addons.inbox import payload, stops
from lem.app.tasks import plans
from lem.store import tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.addons.inbox.records import Entry, Wait
    from lem.addons.inbox.source import RowFacts
    from lem.app.sessions.here import Here


def prepare(
    called: Here,
    link: str,
    facts: tuple[RowFacts, ...],
    wait: Wait,
) -> Entry:
    """Find the task's row and any plan it attaches."""
    found = next(fact for fact in facts if fact.row.key == wait.key)
    written = payload.Material(
        plan=plan(called, found) if wait.kind == "plan" else None,
        breaker=document(called, found)
        if wait.kind == "breaker" and wait.session
        else None,
    )
    target = f"{link.rstrip('/')}/tasks/{wait.task}"
    return payload.message(wait, found, str(called.where.checkout), target, written)


def plan(called: Here, found: RowFacts) -> str | None:
    """The plan path is relative to the task's worktree, or the checkout."""
    workspace = called.where
    named = plans.found(workspace, found.look.record, tasks.every(workspace.state))
    cwd = called.worktree(found.row.task) or workspace.checkout
    return str(cwd / named) if named else None


def document(called: Here, found: RowFacts) -> str | None:
    """Read the held breaker's document inside the task folder, if it reads."""
    breaker = stops.current(found)
    if breaker is None:
        return None
    try:
        return read_document(called.folder(found.row.task), breaker.document)
    except OSError, UnicodeError:
        return None


def read_document(folder: Path, name: str) -> str | None:
    """Use only a document in the task's folder."""
    root = folder.resolve()
    path = (root / name).resolve()
    if not path.is_relative_to(root):
        return None
    return path.read_text(encoding="utf-8").strip() or None
