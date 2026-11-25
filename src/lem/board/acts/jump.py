"""`POST /HOST/WORKSPACE/agterm/SESSION`: the jump to a task's session, on the owner's click on
a page of this Mac (`serve.agterm_act` on `main`; `surfaces.md` B).

agterm gives a page served over http no bridge, so the page asks the server, which selects the
session through the terminal (`Terminal.select`, the owner's act only). Only the session Lem
opened last for a task of the workspace is taken; through the tailnet door there is no jump, as
the phone is not this Mac. The answer is JSON, `{"done": true, "said": ...}` or `{"done":
false, "said": ...}`, which the page shows beside its button.
"""

from http import HTTPStatus
from typing import TYPE_CHECKING

from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse

from lem.app.sessions import here, log
from lem.board.acts import asker
from lem.board.pages import place
from lem.kernel.errors import Fault
from lem.store import places, tasks

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.responses import Response


DOOR = "The jump to a session is for a page on this Mac: the phone has no agterm."
NONE = "That is no session of this workspace's tasks."
SWITCHED = "Switched to the session."


def answered(said: str, status: HTTPStatus, *, done: bool) -> JSONResponse:
    """The answer the page reads: whether it was done, and the line."""
    return JSONResponse({"done": done, "said": said}, status_code=status)


def named(space: places.Workspace, session: str) -> bool:
    """Whether `session` is the newest session Lem opened for a task of the workspace."""
    folders = (
        places.task_folder(space.state, record.task.slug)
        for record in tasks.every(space.state)
    )
    newest = (log.newest_open(log.read(folder)) for folder in folders)
    return any(opened and log.same(opened.session, session) for opened in newest)


def selected(space: places.Workspace, session: str) -> str | None:
    """Select the session in agterm; None when it was done, else why not."""
    if not named(space, session):
        return NONE
    try:
        here.bound(space.checkout).ports.terminal.select(session)
    except Fault as fault:
        return f"agterm did not switch: {fault}."
    return None


async def endpoint(request: Request) -> Response:
    """Select the session of the address, and say what came of it."""
    if asker.door(request):
        return answered(DOOR, HTTPStatus.FORBIDDEN, done=False)
    refused = asker.refusal(request)
    if refused is not None:
        return answered(refused, HTTPStatus.FORBIDDEN, done=False)
    space = place.workspace(request)
    session = request.path_params["session"]
    said = await run_in_threadpool(selected, space, session)
    if said is not None:
        return answered(said, HTTPStatus.UNPROCESSABLE_ENTITY, done=False)
    return answered(SWITCHED, HTTPStatus.OK, done=True)
