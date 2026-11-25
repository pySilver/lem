"""The task's newest session while it still carries the task, and the refusal of an agterm
that does not answer."""

from typing import TYPE_CHECKING

from lem.app.sessions import log, seen
from lem.kernel import clock
from lem.kernel.errors import Refusal
from lem.ports.faults import Unanswered

if TYPE_CHECKING:
    from lem.app.sessions.here import Here


def live_session(here: Here, slug: str) -> str | None:
    """The task's newest session if it still carries the task at the time of the pick."""
    opened = log.newest_open(log.read(here.folder(slug)))
    if opened is None:
        return None
    try:
        shown = seen.look(here)
    except Unanswered as error:
        raise unreachable(error) from error
    return opened.session if shown.carries(opened, clock.now()) else None


def unreachable(error: Unanswered) -> Refusal:
    """The refusal of a picker agterm cannot show."""
    return Refusal(
        "terminal",
        f"agterm did not answer: {error.said}",
        "start the picker from an agterm chord with agtermctl installed (Help > Install "
        "Command Line Tool); lem picker --list prints the rows",
    )
