"""`POST /HOST/WORKSPACE/start`: a new task on the owner's word from the board, from his words (the
form of "+", `words`) or from a backlog item ("Start a task", `item`, its path from the main
checkout) (`serve.act_start` on `main`; `surfaces.md` B).

The task is `lem task open SLUG --ask ASK`, with his words, or the item's path, as its ask, and
its session `lem session open SLUG --why new`, with no focus. The workspace's claim lock holds
the scan of every record with the new one (`app/tasks/open.py`), so an item two starts name
gets one task. A slug of a task that did not end is refused, and so is an item a task holds.
"""

from typing import TYPE_CHECKING

from starlette.concurrency import run_in_threadpool

from lem.app.sessions import here, opening
from lem.app.tasks import open as opened
from lem.board.acts import acting, back, noting, plugin, starting
from lem.board.acts.asked import Asked, refused
from lem.board.acts.notes import Note
from lem.kernel.errors import Fault, Refusal
from lem.store import tasks

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.responses import Response

    from lem.app.tasks.opening import Asked as Opening

ACT = "start"


def session_said(asked: Asked, slug: str) -> str:
    """Open the new task's session, and say so."""
    try:
        made = opening.open_session(
            here.bound(asked.checkout), slug, "new", None, asked.now
        )
    except (Refusal, Fault) as error:
        return f"The task {slug} is on record, and its session did not open: {error}."
    return (
        f"Lem opened the session {made.name} in agterm, at the end of its workspace. "
        "Its agent reads the ask, and takes its type and its track."
    )


def task_of(asked: Asked) -> Opening:
    """Open the task the form names, and give what it opened with."""
    given = starting.opening_of(asked, tasks.every(asked.state))
    plugin.checked(asked.checkout)
    opened.opened(asked.checkout, given)
    return given


def started(asked: Asked) -> Note:
    """Open the task and its session, and the note, which names the task once it is on
    record."""
    try:
        given = task_of(asked)
    except Refusal as refusal:
        return refused(ACT, None, refusal)
    entry = noting.act_of(ACT, asked.asker, asked.now)
    noting.noted(asked.state, given.slug, entry)
    said = session_said(asked, given.slug)
    return Note(task=given.slug, act=ACT, state="done", said=said)


async def endpoint(request: Request) -> Response:
    """Start the task, then its page with the note; a refused start goes back to the form or
    the backlog."""
    asked = await acting.asked_of(request)
    if not isinstance(asked, Asked):
        return asked
    note = await run_in_threadpool(started, asked)
    if note.task is not None:
        return back.to_task(request, note.task, note, None)
    view = "backlog" if asked.given.path else "new"
    return back.to_view(request, view, note)
