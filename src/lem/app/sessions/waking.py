"""`lem session wake`: a line `lem: SLUG WHY` to the left pane of the task's live session, or a new
session when none carries it (`session.cmd_wake` on `main`).

The agent reads the task's files, never the line. A wake keeps the pull request's head it was
for, so that a conflict is woken once for each head. With no live session it opens one, as
`open --why WHY`; but the owner's act on a task that then gets no session (a park) has nothing to
wake, and is no refusal; and a thing of the task in the owner's Inbox opens no session, since it
waits there for the session that comes. A task two releases back gets no line but the one
after its merge, whose session cleans it up. The guard's status message is `guard_steps.status`.
"""

from typing import TYPE_CHECKING

from lem.app.sessions import log, opening, queued, seen
from lem.app.sessions.acts import Wake, WakeWhy
from lem.app.tasks import release
from lem.records.base import Frozen
from lem.store import tasks

if TYPE_CHECKING:
    from datetime import datetime

    from lem.app.sessions.here import Here


class Woken(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """The wake: the session it reached or opened, why, whether a line went to a live session,
    and whether a session was opened."""

    task: str
    session: str | None
    why: str
    woke: bool
    opened: bool
    say: str


def wake(here: Here, slug: str, why: WakeWhy, head: str | None, now: datetime) -> Woken:
    """Send the line to the task's live session, or open one."""
    if why != "merged":
        queued.release_stop(release.checked(here.where.state, slug).task)
    newest = log.newest_open(log.read(here.folder(slug)))
    pane = seen.look(here).carries(newest, now)
    if newest is None or pane is None:
        return opened(here, slug, why, head, now)
    line = f"lem: {slug} {why}"
    here.ports.terminal.tell(newest.session, line)
    woke = Wake(at=now, session=newest.session, why=why, head=head)
    log.reached(here.folder(slug), woke)
    return Woken(
        task=slug,
        session=newest.session,
        why=why,
        woke=True,
        opened=False,
        say=f"the session `{pane.name}` of {slug} got `{line}`",
    )


def opened(
    here: Here, slug: str, why: WakeWhy, head: str | None, now: datetime
) -> Woken:
    """With no live session: nothing for the Inbox or a task that gets no session on the
    owner's act, else a new session."""
    task = tasks.read(here.where.state, slug).task
    gets = here.phase_or_none(task) is not None
    if why == "inbox" or (why == "owner" and not gets):
        said = f"no session of {slug} runs, and nothing opens one for this wake"
        return Woken(
            task=slug, session=None, why=why, woke=False, opened=False, say=said
        )
    made = opening.open_session(here, slug, why, None, now)
    if head:
        woke = Wake(at=now, session=made.session, why=why, head=head)
        log.reached(here.folder(slug), woke)
    return Woken(
        task=slug,
        session=made.session,
        why=why,
        woke=False,
        opened=not made.already,
        say=made.said(),
    )
