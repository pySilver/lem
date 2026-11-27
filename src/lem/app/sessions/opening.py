"""`lem session open`: open the task's session for the phase its record gives, with no focus, or
give the one that still carries it.

Under the task's own lock (`session.lock` in its folder), so that a click and a duty of the board
never open two. When the task's newest session still carries it (`seen.Seen.carries`: listed, with
an agent in its main pane, or opened under a minute ago), that one is given with `already`; a
session whose agent ended leaves a shell, and the new one opens beside it. Otherwise the brief
(`session.md`) is written, and the session opens in the main checkout, whose Claude Code setup
(the plugin, the folder's trust, its settings) is the developer's: the agent works in the task's
worktree by its path. Its seat is `seats.session`; the harness writes the launch line, with the
compaction number and `--plugin-dir` where the project has no install of the plugin. The open is
put on record at once: the session exists from then on. A queued task opens only once its turn
came (`queued.behind`), but a feature for its sync: it takes in its base while it waits.
"""

from typing import TYPE_CHECKING

from lem.app.sessions import brief, log, placing, queued, seating, seen
from lem.app.sessions.acts import Open
from lem.app.sessions.phase import Phase
from lem.kernel import locks, paths
from lem.ports.harness import Seat
from lem.records.base import Frozen
from lem.store import tasks

if TYPE_CHECKING:
    from datetime import datetime

    from lem.app.sessions.here import Here
    from lem.records.task import Task

LOCK = "session.lock"


class Opened(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """The task's session: its id, name and phase, whether it ran already, and where."""

    task: str
    session: str
    name: str
    phase: Phase
    already: bool
    workspace: str | None = None

    def said(self) -> str:
        """The line for the owner."""
        if self.already:
            return f"{self.task} already runs in the session `{self.name}`"
        return (
            f"{self.task} is open in its own session `{self.name}`, phase {self.phase}, at "
            "the end of the workspace"
        )


def open_session(
    here: Here, slug: str, why: str, replacing: str | None, now: datetime
) -> Opened:
    """Open the task's session, or give the one that carries it but `replacing`."""
    folder = here.folder(slug)
    tasks.read(here.where.state, slug)
    with locks.held(folder / LOCK):
        return opened_held(here, slug, why, replacing, now)


def opened_held(
    here: Here, slug: str, why: str, replacing: str | None, now: datetime
) -> Opened:
    """`open_session` under the task's lock, which the restart holds already."""
    task = tasks.read(here.where.state, slug).task
    phase = here.phase(task)
    if not queued.syncs(here, task, why):
        queued.behind(here, task)
    running = already(here, task, phase, replacing, now)
    return running or launched(here, task, phase, why, now)


def already(
    here: Here, task: Task, phase: Phase, replacing: str | None, now: datetime
) -> Opened | None:
    """The task's newest session while it still carries the task, but the one `replacing`."""
    newest = log.newest_open(log.read(here.folder(task.slug)))
    if newest is None or log.same(newest.session, replacing):
        return None
    pane = seen.look(here).carries(newest, now)
    if pane is None:
        return None
    return Opened(
        task=task.slug,
        session=newest.session,
        name=pane.name or newest.name,
        phase=phase,
        already=True,
        workspace=newest.workspace,
    )


def launched(here: Here, task: Task, phase: Phase, why: str, now: datetime) -> Opened:
    """Write the brief, open the session on the launch line, and put it on record."""
    made = placing.opening(here, task, line_for(here, task, phase, why))
    session = here.ports.terminal.open(made)
    noted = Open(
        at=now,
        session=session,
        name=task.slug,
        phase=phase,
        why=why,
        workspace=made.workspace,
    )
    log.reached(here.folder(task.slug), noted)
    return Opened(
        task=task.slug,
        session=session,
        name=task.slug,
        phase=phase,
        already=False,
        workspace=made.workspace,
    )


def line_for(here: Here, task: Task, phase: Phase, why: str) -> str:
    """Write the brief, and give the launch line of the session's seat, `seats.session`:
    Claude Code, with the model and the effort it names."""
    facts = brief.facts(here, task, phase, why)
    path = brief.write(here.folder(task.slug), facts)
    checkout = here.where.checkout
    shown = seating.seat_of("session", checkout, here.home)
    seat = Seat(agent="claude", model=shown.model, effort=shown.effort)
    return here.ports.harness.launch(seat, str(path), checkout, paths.root())
