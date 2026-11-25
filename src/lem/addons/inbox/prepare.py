"""Attach the task's plan and add the workspace's board link."""

from typing import TYPE_CHECKING

from lem.addons.inbox import payload
from lem.app.tasks import plans
from lem.store import tasks

if TYPE_CHECKING:
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
    attachment = plan(called, found) if wait.kind == "plan" else None
    target = f"{link.rstrip('/')}/tasks/{wait.task}"
    return payload.message(wait, found, str(called.where.checkout), target, attachment)


def plan(called: Here, found: RowFacts) -> str | None:
    """The plan path is relative to the task's worktree, or the checkout."""
    workspace = called.where
    named = plans.found(workspace, found.look.record, tasks.every(workspace.state))
    cwd = called.worktree(found.row.task) or workspace.checkout
    return str(cwd / named) if named else None
