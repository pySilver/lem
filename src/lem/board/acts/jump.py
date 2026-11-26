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
from lem.board import listener
from lem.board.pages import place
from lem.kernel.errors import Fault, Refusal
from lem.store import places, survey

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.responses import Response

    from lem.records.record import Record


DOOR = "The jump to a session is for a page on this Mac: the phone has no agterm."
NONE = "That is no session of this workspace's tasks."
SWITCHED = "Switched to the session."


def answered(said: str, status: HTTPStatus, *, done: bool) -> JSONResponse:
    """The answer the page reads: whether it was done, and the line."""
    return JSONResponse({"done": done, "said": said}, status_code=status)


def named(space: places.Workspace, session: str) -> str | None:
    """The session Lem opened last for a task of the workspace that `session` names, as Lem
    keeps its id, or None; a session no readable task names is refused while a record does
    not read, since that task may be the one (decision 30)."""
    records, unread = survey.records(space.state)
    kept = opened_last(space, records, session)
    if kept is None:
        survey.require_complete(survey.warnings(space.state, unread))
    return kept


def opened_last(
    space: places.Workspace, records: tuple[Record, ...], session: str
) -> str | None:
    """The session of `records` whose newest open `session` names, as Lem keeps its id."""
    folders = (places.task_folder(space.state, record.task.slug) for record in records)
    opens = (log.newest_open(log.read(folder)) for folder in folders)
    ids = (one.session for one in opens if one is not None)
    return next((kept for kept in ids if log.same(kept, session)), None)


def selected(space: places.Workspace, session: str) -> str | None:
    """Select the session in agterm; None when it was done, else why not, with the
    repair."""
    try:
        kept = named(space, session)
    except Refusal as refusal:
        return f"{refusal.why} {refusal.fix}"
    if kept is None:
        return NONE
    try:
        here.bound(space.checkout).ports.terminal.select(kept)
    except Fault as fault:
        return f"agterm did not switch: {fault}."
    return None


async def endpoint(request: Request) -> Response:
    """Select the session of the address, and say what came of it."""
    if listener.at_door(request):
        return answered(DOOR, HTTPStatus.FORBIDDEN, done=False)
    refused = listener.act_refusal(request)
    if refused is not None:
        return answered(refused, HTTPStatus.FORBIDDEN, done=False)
    space = place.workspace(request)
    session = request.path_params["session"]
    said = await run_in_threadpool(selected, space, session)
    if said is not None:
        return answered(said, HTTPStatus.UNPROCESSABLE_ENTITY, done=False)
    return answered(SWITCHED, HTTPStatus.OK, done=True)
