"""The task's newest session as `lem session list` gives it, and the refusal of an agterm that
does not answer."""

from typing import TYPE_CHECKING

from lem.app.sessions import listing
from lem.kernel.errors import Refusal
from lem.ports.faults import Unanswered

if TYPE_CHECKING:
    import datetime as dt

    from lem.app.sessions.here import Here


def live_session(here: Here, slug: str, now: dt.datetime) -> str | None:
    """The task's newest session when it lives with its agent in it, else None."""
    try:
        found = listing.list_sessions(here, now)
    except Unanswered as error:
        raise unreachable(error) from error
    mine = (one for one in found if one.task == slug)
    return next((one.session for one in mine if lives(one)), None)


def lives(entry: listing.Listed) -> bool:
    """Whether a task's newest session lives with its agent in it."""
    return entry.live and entry.agent is True


def unreachable(error: Unanswered) -> Refusal:
    """The refusal of a picker agterm cannot show."""
    return Refusal(
        "terminal",
        f"agterm did not answer: {error.said}",
        "start the picker from an agterm chord with agtermctl installed (Help > Install "
        "Command Line Tool); lem picker --list prints the rows",
    )
