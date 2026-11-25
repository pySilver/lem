"""`lem session close-job`: the last step of a scheduled night or retro, whose session no task
owns: close it once the owner has left it.

Its session is the caller's or the one named. It refuses a session that Lem opened for a task,
with the line that closes it under its task, and a session whose agent no job started with the
job's line as its last word (`agents.job_line`): a session where the owner typed `/lem retro` into
an agent he started himself stays his. It puts nothing on record: a record names its task, and a
job's session has none.
"""

from typing import TYPE_CHECKING

from lem.app.sessions import agents, log, seen
from lem.app.sessions.acts import Open
from lem.kernel.errors import Refusal
from lem.records.base import Frozen
from lem.store import tasks

if TYPE_CHECKING:
    from collections.abc import Callable

    from lem.app.sessions.here import Here


class JobClosed(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """The job's session, its line, and whether Lem closed it (false: agterm had it no
    more)."""

    session: str
    job: str | None
    closed: bool


type Pause = Callable[[float], None]


def close_job(here: Here, named: str | None, every: float, pause: Pause) -> JobClosed:
    """Close the job's session once the owner has left it."""
    session = named or here.caller
    if not session:
        raise Refusal(
            "no-session",
            "no session to close: this runs in no session of agterm",
            "run it in the job's own agterm session, or name it with --session ID",
        )
    owned(here, session)
    line = job_of(here, session)
    pane = seen.listed(here).get(session.upper())
    while pane is not None and pane.selected:
        pause(every)
        pane = seen.listed(here).get(session.upper())
    if pane is None or line is None:
        return JobClosed(session=session, job=line, closed=False)
    here.ports.terminal.close(pane.id, when_unselected=True)
    return JobClosed(session=session, job=line, closed=True)


def owned(here: Here, session: str) -> None:
    """Refuse a session that Lem opened for a task: it closes under its task."""
    for record in tasks.every(here.where.state):
        folder = here.folder(record.task.slug)
        acts = log.of_session(log.read(folder), session)
        if any(isinstance(act, Open) for act in acts):
            slug = record.task.slug
            raise Refusal(
                "task-session",
                f"{session} is the session of the task {slug}, and a task's session closes "
                "under its task",
                f"lem session close {slug} --session {session} --why ended --when-unselected",
            )


def job_of(here: Here, session: str) -> str | None:
    """The job's line of the session; refused for one no job started, None for one agterm
    has no more."""
    found = seen.look(here).grounds
    if session.upper() not in found:
        return None
    ground = found[session.upper()]
    line = agents.job_line(ground)
    if line is None:
        raise Refusal(
            "not-a-job",
            f"the session {session} is the owner's: no scheduled job started its agent for "
            f"this run, since its command {ground!r} does not end in "
            "/lem night, /lem night N or /lem retro",
            "it stays open, and the owner closes it himself",
        )
    return line
