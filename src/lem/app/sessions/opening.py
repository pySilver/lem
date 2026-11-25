"""`lem session open`: open the task's session for the phase its record gives, with no focus, or
give the one that runs.

Under the task's own lock (`session.lock` in its folder), so that a click and a duty of the board
never open two. When the terminal still lists the task's newest session, that one is given with
`already`. Otherwise the brief (`session.md`) is written, and the session opens in the main
checkout, whose Claude Code setup (the plugin, the folder's trust, its settings) is the
developer's: the agent works in the task's worktree by its path. The open is put on record at
once: the session exists from then on.
"""

from typing import TYPE_CHECKING

from lem.app.sessions import brief, opened, placing
from lem.app.sessions.phase import Phase
from lem.kernel import locks, paths
from lem.ports.harness import Seat
from lem.records.base import Frozen
from lem.store import tasks

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path

    from lem.app.sessions.here import Here
    from lem.records.task import Task

LOCK = "session.lock"
# The agent of a task's session; the model and effort that `seats.session` names are the step
# `settings`'s.
SEAT = Seat(agent="claude")


class Opened(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """The task's session: its id, name and phase, whether it ran already, and where."""

    task: str
    session: str
    name: str
    phase: Phase
    already: bool
    workspace: str | None = None


def open_session(
    here: Here, slug: str, why: str, replacing: str | None, now: datetime
) -> Opened:
    """Open the task's session, or give the one that runs but `replacing`."""
    folder = here.folder(slug)
    tasks.read(here.where.state, slug)
    with locks.held(folder / LOCK):
        task = tasks.read(here.where.state, slug).task
        phase = here.phase(task)
        placing.behind(here, task)
        running = already(here, folder, phase, replacing)
        if running is not None:
            return running
        return launched(here, task, phase, why, now)


def already(
    here: Here, folder: Path, phase: Phase, replacing: str | None
) -> Opened | None:
    """The task's newest session while the terminal lists it, but the one `replacing`."""
    panes = placing.listed(here)
    newest = opened.newest_open(opened.read(folder))
    if newest is None or newest.session == replacing or newest.session not in panes:
        return None
    return Opened(
        task=folder.name,
        session=newest.session,
        name=panes[newest.session].name,
        phase=phase,
        already=True,
        workspace=newest.workspace,
    )


def launched(here: Here, task: Task, phase: Phase, why: str, now: datetime) -> Opened:
    """Write the brief, open the session on the launch line, and put it on record."""
    folder = here.folder(task.slug)
    path = brief.write(folder, facts(here, task, phase, why))
    session, workspace = in_terminal(here, task, path)
    noted = opened.Open(
        at=now,
        session=session,
        name=task.slug,
        phase=phase,
        why=why,
        workspace=workspace,
    )
    opened.append(folder, noted)
    return Opened(
        task=task.slug,
        session=session,
        name=task.slug,
        phase=phase,
        already=False,
        workspace=workspace,
    )


def in_terminal(here: Here, task: Task, path: Path) -> tuple[str, str | None]:
    """Open the session on the launch line of the brief at `path`: its id and workspace."""
    plugin = paths.root()
    checkout = here.where.checkout
    line = here.ports.harness.launch(SEAT, str(path), checkout, plugin)
    made = placing.opening(here, task, line)
    session = here.ports.terminal.open(made)
    return session, made.workspace or placing.workspace_of(here, session)


def said(made: Opened) -> str:
    """The line for the owner."""
    if made.already:
        return f"{made.task} already runs in the session `{made.name}`"
    return (
        f"{made.task} is open in its own session `{made.name}`, phase {made.phase}, at the "
        "end of the workspace"
    )


def facts(here: Here, task: Task, phase: Phase, why: str) -> dict[str, str]:
    """The lines of the brief after its first: the task, its phase and why it opened, and the
    task's folder, main checkout and worktree."""
    worktree = here.worktree(task.slug)
    return {
        "task": task.slug,
        "phase": phase,
        "opened because": why,
        "task directory": str(here.folder(task.slug)),
        "main checkout": str(here.where.checkout),
        "worktree": str(worktree) if worktree else "none yet",
    }
