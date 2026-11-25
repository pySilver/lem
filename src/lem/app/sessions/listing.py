"""`lem session list`: each task's newest session, with the phase its task is in now and the one
it opened in, whether the terminal still has it, whether an agent runs in it, whether the owner
looks at it, whether its newest wake went unanswered, and its signs of work (`session.cmd_list`
on `main`).

A session that no longer carries its task (gone, or a shell its agent left) has no signs: `sign`
and `turn` null, `shell` and `signs` false. The terminal is asked only when a task has a session
on record.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.app.sessions import agents, log, seen, signs
from lem.app.sessions.acts import Close
from lem.app.sessions.phase import Phase
from lem.app.sessions.unheard import Unheard, unheard_of
from lem.records.base import Frozen, Moment
from lem.store import tasks

if TYPE_CHECKING:
    from datetime import datetime

    from lem.app.sessions.acts import Open
    from lem.app.sessions.here import Here
    from lem.records.record import Record


class Listed(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """One task's newest session."""

    task: str
    session: str
    name: str
    phase: Phase | None
    opened_in: str
    why: str
    since: Moment
    workspace: str | None
    live: bool
    agent: bool | None
    selected: bool
    closed: str | None
    unanswered: bool
    unheard: Unheard | None
    sign: Moment | None
    shell: bool
    signs: bool
    turn: str | None


def list_sessions(here: Here, now: datetime) -> tuple[Listed, ...]:
    """Each task's newest session that Lem opened, task by task; the terminal is asked once,
    and only when there is one."""
    opened = opened_tasks(here)
    if not opened:
        return ()
    shown = seen.look(here)
    entries = (entry(here, shown, *pair, now) for pair in opened)
    return tuple(entries)


def opened_tasks(here: Here) -> list[tuple[Record, Open]]:
    """Each task Lem opened a session for, with its newest session."""
    records = tasks.every(here.where.state)
    pairs = ((one, newest(here, one)) for one in records)
    return [(record, found) for record, found in pairs if found]


def newest(here: Here, record: Record) -> Open | None:
    """The newest session Lem opened for the task of `record`."""
    return log.newest_open(log.read(here.folder(record.task.slug)))


def entry(
    here: Here, shown: seen.Seen, record: Record, opened: Open, now: datetime
) -> Listed:
    """The entry of the task of `record`, whose newest session is `opened`."""
    slug = record.task.slug
    pane = shown.pane(opened.session)
    read = read_now(here, shown, slug, opened, now)
    heard = unheard_of(here, slug, opened.session, read, now) if pane else None
    return Listed(
        task=slug,
        session=opened.session,
        name=pane.name if pane else opened.name,
        phase=here.phase_or_none(record.task),
        opened_in=opened.phase,
        why=opened.why,
        since=opened.at,
        workspace=opened.workspace,
        live=pane is not None,
        agent=agents.agent_runs(shown.ground(opened.session)) if pane else False,
        selected=bool(pane and pane.selected),
        closed=closed_why(here, slug, opened.session),
        unanswered=heard is not None,
        unheard=heard,
        **msgspec.structs.asdict(read),
    )


def read_now(
    here: Here, shown: seen.Seen, slug: str, opened: Open, now: datetime
) -> signs.Read:
    """The signs of the session while it carries its task, else none."""
    if shown.carries(opened, now) is None:
        return signs.Read()
    return signs.read_signs(here, slug, opened.session)


def closed_why(here: Here, slug: str, session: str) -> str | None:
    """Why Lem closed the session `session`, or None while it did not."""
    acts = log.of_session(log.read(here.folder(slug)), session)
    closes = [act.why for act in acts if isinstance(act, Close)]
    return closes[0] if closes else None
