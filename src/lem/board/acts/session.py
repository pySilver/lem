"""`POST /HOST/WORKSPACE/tasks/SLUG/session`: "Open a session", on the owner's click
(`serve.act_session` on `main`).

A task none of whose sessions carries it gets one, `lem session open SLUG --why dead` when it had
one and `--why owner` when it never did, with no focus, at the end of its workspace of agterm. A
task whose session the guard stopped gets a fresh one beside that session, `lem session open
SLUG --why stopped`, while the stop stands; the guard's one more look may open nothing and say
why. A task whose session carries it is refused: the owner goes to that session.
"""

from typing import TYPE_CHECKING

from lem.app.sessions import here, log, opening
from lem.app.sessions.acts import Stopped
from lem.board.acts import acting, noting, restarting
from lem.board.acts.asked import refused
from lem.board.acts.notes import Note
from lem.kernel.errors import Refusal
from lem.store import places

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.responses import Response

    from lem.app.sessions.acts import Act
    from lem.board.acts.asked import Asked

ACT = "session"


def stopped(acts: tuple[Act, ...], session: str) -> bool:
    """Whether the guard put a stop of the session on record."""
    return any(
        isinstance(act, Stopped) and log.same(act.session, session) for act in acts
    )


def fresh(asked: Asked, *, before: bool) -> str:
    """A session of a task none of whose sessions carries it."""
    bound = here.bound(asked.checkout)
    why = "dead" if before else "owner"
    made = opening.open_session(bound, asked.slug, why, None, asked.now)
    if made.already:
        said = f"No session of {asked.slug} was opened: its session “{made.name}” runs."
        raise Refusal("runs", said, "go to it in agterm")
    return (
        f"A session of the task opened in agterm, “{made.name}”, at the end of its "
        f"workspace. {restarting.GOES_ON}"
    )


def said_of(asked: Asked) -> str:
    """Open the session the task needs, and say so."""
    acts = log.read(places.task_folder(asked.state, asked.slug))
    newest = log.newest_open(acts)
    said = None
    if newest is not None and stopped(acts, newest.session):
        said = restarting.beside(asked)
    if said is None:
        said = fresh(asked, before=newest is not None)
    entry = noting.act_of(ACT, asked.asker, asked.now)
    noting.noted(asked.state, asked.slug, entry)
    return said


def opened(asked: Asked) -> Note:
    """Open a session of the task, and its note."""
    try:
        said = said_of(asked)
    except Refusal as refusal:
        return refused(ACT, asked.slug, refusal)
    return Note(task=asked.slug, act=ACT, state="done", said=said)


async def endpoint(request: Request) -> Response:
    """Open a session of the task, and go to its page with the note."""
    return await acting.on_task(request, opened)
