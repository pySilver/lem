"""What this Mac's board tells a joined board of its agterm, as reads: `GET
/HOST/WORKSPACE/agterm/SESSION`, the agterm id of a session Lem opened for a task of the
workspace, and `GET /api/agterm`, whether this launch of agterm runs Live sessions, which a
session attached from another Mac needs.

The Mac where the owner's agterm runs asks before it attaches the session over ssh
(`peers/jump.py`), and `lem doctor` there asks for each joined machine. A read carries no act:
it passes the door as every read of the board does.
"""

from http import HTTPStatus
from typing import TYPE_CHECKING

from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse

from lem.adapters import agterm_remote
from lem.board.acts import jump
from lem.board.pages import place
from lem.kernel.errors import Fault, Refusal
from lem.records.base import Frozen

if TYPE_CHECKING:
    from collections.abc import Mapping

    from starlette.requests import Request

    from lem.store.places import Workspace

LIVE = "live"
GONE = "gone"


class Origin(Frozen, frozen=True, kw_only=True):
    """A session of a task in this Mac's agterm, whether agterm runs Live sessions (None when it
    did not say), and why it did not say."""

    session: str
    live: bool | None = None
    said: str = ""


class Told(Frozen, frozen=True, kw_only=True):
    """Why this board names no session: `gone` for none of the workspace's tasks, else the code
    of the refusal of a record it could not read, with its why and its fix."""

    code: str
    why: str = ""
    fix: str = ""


def live(environ: Mapping[str, str]) -> tuple[bool | None, str]:
    """Whether this launch of agterm runs Live sessions, or None and why it did not say."""
    try:
        mode = agterm_remote.restore_mode(environ)
    except Fault as fault:
        return None, str(fault)
    if mode is None:
        return None, "agterm's restore mode named no active mode"
    return mode == LIVE, ""


def found(space: Workspace, session: str, environ: Mapping[str, str]) -> Origin | Told:
    """The task's session that `session` names, or why there is none, with the repair."""
    try:
        kept = jump.named(space, session)
    except Refusal as refusal:
        return Told(code=refusal.code, why=refusal.why, fix=refusal.fix)
    if kept is None:
        return Told(code=GONE, why=jump.NONE)
    running, said = live(environ)
    return Origin(session=kept, live=running, said=said)


async def session(request: Request) -> JSONResponse:
    """The agterm id of a task's session in this workspace; 404 when no task names it, 409 when
    a record that may name it does not read."""
    space = place.workspace(request)
    named = request.path_params["session"]
    seen = await run_in_threadpool(found, space, named, request.app.state.environ)
    if isinstance(seen, Told):
        status = HTTPStatus.NOT_FOUND if seen.code == GONE else HTTPStatus.CONFLICT
        told = {"code": seen.code, "why": seen.why, "fix": seen.fix}
        return JSONResponse(told, status_code=status)
    return JSONResponse({"session": seen.session, "live": seen.live, "said": seen.said})


async def agterm(request: Request) -> JSONResponse:
    """Whether this Mac's agterm runs Live sessions; null, and why, when it does not say."""
    environ = request.app.state.environ
    running, said = await run_in_threadpool(live, environ)
    return JSONResponse({"live": running, "said": said})
