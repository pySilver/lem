"""`lem session wait --first-line`: the task's first line, which the session where the owner typed
the request says, once the task's own session put its read on record (`session.cmd_first_line`
on `main`).

It ends with the line when the record has the read (`Shape`): the task named first, its type
with the owner's words, and its track. It ends with no line, and why, when the task is a night's
(the night's report names it), when it is parked or ended before its read, when its order waits
for the owner, when its session is gone, and after the bound.
"""

from typing import TYPE_CHECKING

from lem.app.sessions import waiting
from lem.records.base import Frozen
from lem.records.holds import OwnerHold, Parked
from lem.store import tasks

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime

    from lem.app.sessions.here import Here
    from lem.records.task import Task

# The words of each track in the first line.
TRACKS = (("small", "Fast track"), ("full", "Standard track"))
ENDED = frozenset(("landed", "answered", "dropped"))


class FirstLine(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """The task's first line as another session says it, or None with why; whether its
    session is gone."""

    task: str
    say: str | None
    gone: bool = False
    why: str | None = None


def ended(task: Task) -> FirstLine | None:
    """How the wait ends by the task's record now, or None while it waits."""
    slug = task.slug
    if task.shape is not None and task.night is None:
        return FirstLine(task=slug, say=line_of(task))
    why = ended_why(task)
    return None if why is None else FirstLine(task=slug, say=None, why=why)


def ended_why(task: Task) -> str | None:
    """Why no line comes, or None while one may."""
    slug = task.slug
    if task.shape is not None:
        return f"{slug} is a task of the night: the night's report names it"
    parked = isinstance(task.hold, Parked)
    if parked or task.status in ENDED:
        state = "parked" if parked else task.status
        return f"{slug} is {state} before its first line, so there is no line to say"
    if isinstance(task.hold, OwnerHold) and task.hold.on == "order":
        return (
            f"{slug} waits for the owner's order, since his words name no open task Lem can "
            "tell; its first line comes with his answer, in its own session"
        )
    return None


def line_of(task: Task) -> str:
    """The first line as another session says it: the task first, its type and the owner's
    words, its track."""
    shape = task.shape
    if shape is None:
        return task.slug
    track = dict(TRACKS)[shape.track]
    words = task.ask.replace('"', "'")
    kind = shape.type
    return f'{task.slug} · {kind}: "{words}". {track}: {shape.why}'


type Asked = tuple[str, float, float]


def first_line(
    here: Here,
    asked: Asked,
    clock: Callable[[], datetime],
    pause: Callable[[float], None],
) -> FirstLine:
    """Wait for the task's first line, its session's end, or the bound; `asked` is the task,
    the seconds between two looks, and the bound."""
    slug, every, bound = asked
    began = clock()
    found = None
    while found is None:
        found = looked(here, slug, bound, began, clock())
        if found is None:
            pause(every)
    return found


def looked(
    here: Here, slug: str, bound: float, began: datetime, now: datetime
) -> FirstLine | None:
    """One look: how the wait ends now, or None while it goes on."""
    found = ended(tasks.read(here.where.state, slug).task)
    if found is not None:
        return found
    session = waiting.gone_session(here, slug, now)
    if session is not None:
        why = (
            f"the session of {slug} is gone before its first line: lem session open {slug} "
            "--why dead opens a fresh one"
        )
        return FirstLine(task=slug, say=None, gone=True, why=why)
    if (now - began).total_seconds() < bound:
        return None
    minutes = bound / 60
    why = (
        f"no first line of {slug} came in {minutes:g} minutes: the board shows it when its "
        "session writes it"
    )
    return FirstLine(task=slug, say=None, why=why)
