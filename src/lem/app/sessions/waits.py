"""The loop of `lem session wait --until STATES | --event KIND`: one look at each turn, then a
pause, until one of the ends of `waiting` comes."""

from pathlib import Path
from typing import TYPE_CHECKING

import msgspec

from lem.app.sessions import waiting
from lem.records.base import Frozen
from lem.store import tasks

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime

    from lem.app.sessions.here import Here

type Clock = Callable[[], datetime]


class Asked(Frozen, frozen=True, kw_only=True):
    """The wait asked for: the task, the statuses or the kind that end it, the companion and
    the quiet file that end it too, and the seconds between two looks."""

    slug: str
    until: tuple[str, ...] = ()
    event: str | None = None
    companion: str | None = None
    quiet: str | None = None
    every: float


def wait_for(
    here: Here, asked: Asked, clock: Clock, pause: Callable[[float], None]
) -> waiting.Waited:
    """Look until the wait ends; each look reads the files and the terminal again."""
    before = waiting.counted(here, asked.slug, asked.event)
    began = clock()
    ended = None
    while ended is None:
        ended = looked(here, asked, before, began, clock())
        if ended is None:
            pause(asked.every)
    return ended


def looked(
    here: Here, asked: Asked, before: int, began: datetime, now: datetime
) -> waiting.Waited | None:
    """One look: how the wait ends now, or None while it goes on."""
    task = tasks.read(here.where.state, asked.slug).task
    base = waiting.Waited(task=task.slug, status=task.status, since=task.since)
    entry = (
        waiting.entry_of(here, asked.slug, asked.event, before) if asked.event else None
    )
    if entry is not None or task.status in asked.until:
        return msgspec.structs.replace(base, entry=entry)
    return gone(here, asked, base, now) or quiet(asked, base, began, now)


def gone(
    here: Here, asked: Asked, base: waiting.Waited, now: datetime
) -> waiting.Waited | None:
    """The end by a companion or the task's session that is gone."""
    slug = asked.slug
    companion = asked.companion
    if companion and waiting.gone_companion(here, companion):
        say = (
            f"the companion {companion} of {slug} is gone before the status came, and the "
            f"task is {base.status}: read the plan's talk before anything else"
        )
        return msgspec.structs.replace(base, gone=True, companion=companion, say=say)
    session = waiting.gone_session(here, slug, now)
    if session is None:
        return None
    say = (
        f"the session of {slug} is gone, and the task is {base.status}: nothing goes on with "
        f"it until lem session open {slug} --why dead opens a fresh one"
    )
    return msgspec.structs.replace(base, gone=True, session=session, say=say)


def quiet(
    asked: Asked, base: waiting.Waited, began: datetime, now: datetime
) -> waiting.Waited | None:
    """The end by a file that has not changed for QUIET_SECONDS since the later of its last
    change and the wait's start."""
    if asked.quiet is None:
        return None
    since = max(changed(asked.quiet) or 0, began.timestamp())
    if now.timestamp() - since < waiting.QUIET_SECONDS:
        return None
    say = (
        f"{asked.quiet} has not changed for 45 minutes and no status came: read the screen of "
        "each pane of the pair for one of the four errors of a seat, and run the same wait "
        "again when neither shows one"
    )
    return msgspec.structs.replace(base, quiet=asked.quiet, say=say)


def changed(path: str) -> float | None:
    """When the file at `path` last changed, None while it is not there."""
    try:
        return Path(path).stat().st_mtime
    except OSError:
        return None
