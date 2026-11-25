"""Find only the Claude Code id of the task's current live session."""

from typing import TYPE_CHECKING

from lem.app.sessions import log
from lem.store import sessions

if TYPE_CHECKING:
    from lem.app.owner.looking import Looked
    from lem.app.sessions.here import Here
    from lem.model.owner.looks import Look


def claude_of(here: Here, look: Look) -> str | None:
    """The newest non-fork hook record for the current live session."""
    if look.session is None or not look.session.live or look.session.unanswered:
        return None
    slug = look.record.task.slug
    folder = here.folder(slug)
    opened = log.newest_open(log.read(folder))
    since = opened.at if opened else look.session.since
    lines = reversed(sessions.read(folder))
    return next(
        (
            line.claude
            for line in lines
            if line.source != "fork"
            and line.at >= since
            and line.task == slug
            and line.claude
        ),
        None,
    )


def live_of(here: Here, seen: Looked) -> dict[str, str]:
    """The live Claude Code sessions able to pick up a reply."""
    return {
        look.record.task.slug: name
        for look in seen.looks
        if (name := claude_of(here, look)) is not None
    }
