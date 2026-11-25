"""`lem session close`: put the close of a task's session on record, then close it.

Never a session the owner has selected: refused, or with `when_unselected` waited for until he
has left it. With a session named, only one that Lem opened for the task, an older one too, since
a handoff closes the one before it. The record comes first, since a session that closes itself
ends with this command; a session the terminal no longer has is put on record as closed and given
as not closed by Lem. A close that waits ends with no close and no record when the session is
woken while it waits (a queued task's `lem: SLUG queue`): it has work again, and the close of its
next change of phase or of its end is the one that closes it.
"""

from typing import TYPE_CHECKING, Literal

from lem.app.sessions import log, seen
from lem.app.sessions.acts import Act, Close, Open, Wake
from lem.kernel.errors import Refusal
from lem.records.base import Frozen

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime
    from pathlib import Path

    from lem.app.sessions.here import Here

type Why = Literal["handoff", "ended", "owner"]


class Closing(Frozen, frozen=True, kw_only=True):
    """The close asked for: the task, the session (else its newest), why, whether to wait
    until the owner left it, and the seconds between two looks."""

    slug: str
    session: str | None = None
    why: Why
    when_unselected: bool = False
    every: float

    def outcome(self, session: str, *, closed: bool, woken: bool = False) -> Closed:
        """The close's outcome for `session`."""
        return Closed(
            task=self.slug, session=session, why=self.why, closed=closed, woken=woken
        )

    def refuse_or_wait(
        self, session: str, name: str, pause: Callable[[float], None]
    ) -> None:
        """Refuse a close of the session the owner looks at, or wait one look when it
        waits."""
        if not self.when_unselected:
            raise Refusal(
                "selected",
                f"the owner has the session {name} selected, and Lem never closes a "
                "session he looks at",
                f"lem session close {self.slug} --session {session} --why {self.why} "
                "--when-unselected closes it once he left it",
            )
        pause(self.every)


class Closed(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """The session, why, whether Lem closed it (false: the terminal had it no more, or it was
    woken), and whether a wake kept it open."""

    task: str
    session: str
    why: Why
    closed: bool
    woken: bool = False


def close_session(
    here: Here,
    closing: Closing,
    pause: Callable[[float], None],
    clock: Callable[[], datetime],
) -> Closed:
    """Close the task's session once nobody looks at it, and put the close on record first."""
    folder = here.folder(closing.slug)
    session = chosen(closing, log.read(folder))
    wakes = woken(folder, session)
    closed = None
    while closed is None:
        if closing.when_unselected and woken(folder, session) > wakes:
            return closing.outcome(session, closed=False, woken=True)
        closed = once(here, closing, session, pause, clock)
    return closing.outcome(session, closed=closed)


def once(
    here: Here,
    closing: Closing,
    session: str,
    pause: Callable[[float], None],
    clock: Callable[[], datetime],
) -> bool | None:
    """One look and, when nobody looks at the session, its close: whether Lem closed it, False
    when the terminal had it no more, None when the owner looks at it and the close waits."""
    pane = seen.listed(here).get(session.upper())
    if pane is not None and pane.selected:
        closing.refuse_or_wait(session, pane.name, pause)
        return None
    noted(here.folder(closing.slug), session, closing.why, clock)
    if pane is None:
        return False
    here.ports.terminal.close(session, when_unselected=True)
    return None if session.upper() in seen.listed(here) else True


def woken(folder: Path, session: str) -> int:
    """How many wakes of `session` are on record: counted, not timed, since a moment has
    whole seconds and a wake may come in the second the close started."""
    return sum(
        isinstance(act, Wake) for act in log.of_session(log.read(folder), session)
    )


def noted(folder: Path, session: str, why: Why, clock: Callable[[], datetime]) -> None:
    """Put the close of `session` on record, once."""
    acts = log.of_session(log.read(folder), session)
    if not any(isinstance(act, Close) for act in acts):
        log.append(folder, Close(at=clock(), session=session, why=why))


def chosen(closing: Closing, acts: tuple[Act, ...]) -> str:
    """The session to close: the one named, when Lem opened it for the task, else the task's
    newest."""
    slug = closing.slug
    opens = [act.session for act in acts if isinstance(act, Open)]
    named = closing.session
    mine = [one for one in opens if log.same(one, named)]
    if named is not None and not mine:
        raise Refusal(
            "not-the-tasks",
            f"{named} is no session of {slug}: Lem opened no such session for it",
            "lem session list gives each task's session; close a session under its own "
            f"task, or leave out --session to close {slug}'s newest",
        )
    if not opens:
        raise Refusal(
            "no-session",
            f"no session of {slug} is on record: there is nothing to close",
            "lem session list gives each task's session",
        )
    return mine[0] if mine else opens[-1]
