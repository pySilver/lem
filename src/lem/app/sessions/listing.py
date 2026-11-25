"""`lem session list`: each task's newest session, with the phase its task is in now, whether the
terminal still has it, whether the owner looks at it, and its signs of work.

The signs are those of the newest transcript the `session-start` hook put on record for that
session (its line's `pane`), read through the harness: the newest sign and whether its turn runs.
`signs` is false when no transcript of that session is on record, or when its transcript gave
neither a sign nor a turn (one that does not read, or is gone): the guard then reads the task's
own record alone. Whether an agent still runs in
the session, and a shell command of it, are not read in this slice.
"""

from typing import TYPE_CHECKING

from lem.app.sessions import opened, placing
from lem.app.sessions.phase import Phase
from lem.kernel.errors import Fault, Refusal
from lem.records.base import Frozen, Moment
from lem.store import sessions, tasks

if TYPE_CHECKING:
    from lem.app.sessions.here import Here
    from lem.ports.harness import Signs
    from lem.ports.terminal import Pane
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
    selected: bool
    closed: str | None
    sign: Moment | None
    turn: str | None
    signs: bool


def list_sessions(here: Here) -> tuple[Listed, ...]:
    """Each task's newest session that Lem opened, task by task; the terminal is asked only
    when there is one."""
    records = tasks.every(here.where.state)
    opens = [record for record in records if has_open(here, record)]
    panes = placing.listed(here) if opens else {}
    return tuple(entry(here, record, panes) for record in opens)


def has_open(here: Here, record: Record) -> bool:
    """Whether Lem opened a session for the task of `record`."""
    noted = opened.read(here.folder(record.task.slug))
    return opened.newest_open(noted) is not None


def entry(here: Here, record: Record, panes: dict[str, Pane]) -> Listed:
    """The entry of the task of `record`, a task Lem opened a session for."""
    slug = record.task.slug
    noted = opened.read(here.folder(slug))
    newest = opened.newest_open(noted)
    if newest is None:
        raise Fault(f"the open of {slug}'s session is gone from its record")
    pane = panes.get(newest.session)
    signs = signs_of(here, slug, newest.session) if pane else None
    return Listed(
        task=slug,
        session=newest.session,
        name=pane.name if pane else newest.name,
        phase=phase_now(here, record),
        opened_in=newest.phase,
        why=newest.why,
        since=newest.at,
        workspace=newest.workspace,
        live=pane is not None,
        selected=bool(pane and pane.selected),
        closed=closed_why(noted, newest.session),
        sign=signs.sign if signs else None,
        turn=signs.turn if signs else None,
        signs=signs is not None,
    )


def phase_now(here: Here, record: Record) -> Phase | None:
    """The phase the task is in now; None for a task that gets no session."""
    try:
        return here.phase(record.task)
    except Refusal:
        return None


def closed_why(noted: tuple[opened.Noted, ...], session: str) -> str | None:
    """Why Lem closed the session `session`, or None while it did not."""
    closes = (line for line in noted if isinstance(line, opened.Close))
    return next((line.why for line in closes if line.session == session), None)


def signs_of(here: Here, slug: str, session: str) -> Signs | None:
    """The signs of the newest transcript of the session `session`; None when none of its
    transcripts is on record, or when it gave neither a sign nor a turn."""
    lines = sessions.read(here.folder(slug))
    claudes = {line.claude for line in lines if line.pane == session}
    found = [
        one for one in here.ports.harness.transcripts(slug) if one.claude in claudes
    ]
    signs = here.ports.harness.signs(found[-1]) if found else None
    if signs is None or (signs.sign is None and signs.turn is None):
        return None
    return signs
