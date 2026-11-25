"""The feed's words of the guard's stop (`session.stopped`, `stop_over_work_said` and
`stop_unrestarted_said` on `main`): a stop that work overtook never stood, and nothing waited;
a stop Lem could not read says so; a readable one says whether a fresh session already took the
stopped one's place.

Work in the second of the stop counts as after it, as the guard's timeline orders them
(`guard_look.order`): only work of an earlier moment, between the status message and the stop,
overtook it.
"""

from typing import TYPE_CHECKING

from lem.app.sessions.guard_rule import ANSWER_SECONDS, OPEN, STOPPED, WORK
from lem.board.views.activity.told import ALERT, BAD, QUIET, SPLIT, Told

if TYPE_CHECKING:
    from lem.app.sessions.acts import Stopped
    from lem.app.sessions.guard_rule import Timeline

ANSWER_MINUTES = ANSWER_SECONDS // 60
HEAD = "The task’s session stopped"
UNREAD = Told(
    BAD,
    ALERT,
    HEAD,
    (
        f"no event of the task in the {ANSWER_MINUTES} minutes after the status message, "
        "and Lem cannot read its session: “Open a session” on the board starts a fresh one"
    ),
)
AGAIN = Told(
    BAD,
    ALERT,
    HEAD,
    (
        "no sign of work after the status message, nor in the fresh session: “Open a "
        "session” on the board starts another"
    ),
)
ALONE = Told(
    BAD,
    ALERT,
    HEAD,
    (
        "no sign of work after the status message, and Lem opened no fresh session by "
        "itself: “Open a session” on the board starts one"
    ),
)
OVERTAKEN = Told(
    QUIET,
    SPLIT,
    "Lem logged a stop of the task’s session, but the task worked",
    (
        "work of the task came after the status message and before the stop, so the stop "
        "does not stand and nothing waits for you"
    ),
)


def stopped(done: Stopped, line: Timeline) -> Told:
    """The stop `done` in the words of where it stands in the task's timeline."""
    place = place_of(done, line)
    if place is not None and not line.stood(place):
        return OVERTAKEN
    if done.unread:
        return UNREAD
    if place is not None and restarted_before(line, place):
        return AGAIN
    return ALONE


def place_of(done: Stopped, line: Timeline) -> int | None:
    """The place of the stop in the timeline, by its moment."""
    places = line.places(STOPPED)
    found = [place for place in places if line.events[place].at == done.at]
    return found[-1] if found else None


def restarted_before(line: Timeline, place: int) -> bool:
    """Whether the guard opened a fresh session in the stopped one's place after the task's
    newest work before the stop at `place`."""
    for event in reversed(line.events[:place]):
        if event.kind == OPEN and event.why == STOPPED:
            return True
        if event.kind == WORK:
            return False
    return False
