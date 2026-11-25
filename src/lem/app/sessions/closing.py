"""`lem session close`: put the close of a task's session on record, then close it.

Never a session the owner has selected: refused, or with `when_unselected` waited for until he
has left it. With a session named, only one that Lem opened for the task. The record comes first,
since a session that closes itself ends with this command; a session the terminal no longer has
is put on record as closed and given as not closed by Lem.
"""

from typing import TYPE_CHECKING, Literal

from lem.app.sessions import opened, placing
from lem.kernel.errors import Refusal
from lem.records.base import Frozen

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime

    from lem.app.sessions.here import Here
    from lem.ports.terminal import Pane

type Why = Literal["handoff", "ended", "owner"]


class Closing(Frozen, frozen=True, kw_only=True):
    """The close asked for: the task, the session (else its newest), why, whether to wait
    until the owner left it, and the seconds between two looks."""

    slug: str
    session: str | None = None
    why: Why
    when_unselected: bool = False
    every: float


class Closed(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """The session, why, and whether Lem closed it (false: the terminal had it no more)."""

    task: str
    session: str
    why: Why
    closed: bool


def close_session(
    here: Here,
    closing: Closing,
    pause: Callable[[float], None],
    clock: Callable[[], datetime],
) -> Closed:
    """Close the task's session once nobody looks at it, and put the close on record."""
    folder = here.folder(closing.slug)
    noted = opened.read(folder)
    session = chosen(closing, noted)
    pane = unselected(here, closing, session, pause)
    if not any(
        isinstance(line, opened.Close) and line.session == session for line in noted
    ):
        opened.append(
            folder, opened.Close(at=clock(), session=session, why=closing.why)
        )
    if pane is not None:
        here.ports.terminal.close(session, when_unselected=True)
    return Closed(
        task=closing.slug, session=session, why=closing.why, closed=pane is not None
    )


def chosen(closing: Closing, noted: tuple[opened.Noted, ...]) -> str:
    """The session to close: the one named, when Lem opened it for the task, else the
    task's newest."""
    slug = closing.slug
    opens = [line.session for line in noted if isinstance(line, opened.Open)]
    if closing.session is not None and closing.session not in opens:
        raise Refusal(
            "not-the-tasks",
            f"{closing.session} is no session of {slug}: Lem opened no such session for it",
            "lem session list gives each task's session; leave out --session to close the "
            "task's newest",
        )
    if not opens:
        raise Refusal(
            "no-session",
            f"no session of {slug} is on record: there is nothing to close",
            "lem session list gives each task's session",
        )
    return closing.session or opens[-1]


def unselected(
    here: Here, closing: Closing, session: str, pause: Callable[[float], None]
) -> Pane | None:
    """The session once the owner has no longer selected it, or None when the terminal has
    it no more; refused while he looks at it, unless the close waits."""
    pane = placing.listed(here).get(session)
    while pane is not None and pane.selected:
        if not closing.when_unselected:
            raise Refusal(
                "selected",
                f"the owner has the session {pane.name} selected, and Lem never closes a "
                "session he looks at",
                f"lem session close {closing.slug} --session {session} --why "
                f"{closing.why} --when-unselected closes it once he left it",
            )
        pause(closing.every)
        pane = placing.listed(here).get(session)
    return pane
