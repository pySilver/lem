"""The ends of `lem session wait` other than a status or an entry: a companion that is gone, the
task's session that is gone, and a file that stays quiet (`session.cmd_wait` on `main`)."""

from pathlib import Path
from typing import TYPE_CHECKING

import msgspec

from lem.app.sessions import waiting

if TYPE_CHECKING:
    from datetime import datetime

    from lem.app.sessions.here import Here
    from lem.app.sessions.waits import Asked

type Moments = tuple[datetime, datetime]


def otherwise(
    here: Here, asked: Asked, base: waiting.Waited, moments: Moments
) -> waiting.Waited | None:
    """The end by a companion, the task's session or a quiet file, or None."""
    pair = companion_end(here, asked, base, moments)
    own = pair or session_end(here, asked, base, moments[1])
    return own or quiet_end(asked, base, moments)


def companion_end(
    here: Here, asked: Asked, base: waiting.Waited, moments: Moments
) -> waiting.Waited | None:
    """The end by a companion of the waiting session that is gone."""
    began, now = moments
    companion = asked.companion
    if not companion or not waiting.gone_companion(here, companion, now - began):
        return None
    say = (
        f"the companion {companion} of {asked.slug} is gone before the status came, and the "
        f"task is {base.status}: read the plan's talk before anything else"
    )
    return msgspec.structs.replace(base, gone=True, companion=companion, say=say)


def session_end(
    here: Here, asked: Asked, base: waiting.Waited, now: datetime
) -> waiting.Waited | None:
    """The end by the task's session that is gone."""
    slug = asked.slug
    session = waiting.gone_session(here, slug, now)
    if session is None:
        return None
    say = (
        f"the session of {slug} is gone, and the task is {base.status}: nothing goes on with "
        f"it until lem session open {slug} --why dead opens a fresh one"
    )
    return msgspec.structs.replace(base, gone=True, session=session, say=say)


def quiet_end(
    asked: Asked, base: waiting.Waited, moments: Moments
) -> waiting.Waited | None:
    """The end by a file that has not changed for QUIET_SECONDS since the later of its last
    change and the wait's start."""
    began, now = moments
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
