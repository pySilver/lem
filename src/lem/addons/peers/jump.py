"""`POST /PEER/WORKSPACE/agterm/SESSION` on the board of the Mac where the owner's agterm runs: the
jump to a task's session of a joined machine, on his click on the task's page that this board
relays (`jump.py` of the board does it for a task of this Mac).

The act is this board's own, never relayed: the joined machine takes no write. The session must
be an agterm id before any command takes it. The act reads on the joined board that the session
is a task's there and whether that agterm runs Live sessions (`origin_read.py`, which
`origin.py` there answers), then shows the session in this Mac's agterm (`attaching.py`), one
jump at a time for each session (`attach_guard.py`). The ssh destination is the machine's name on
the tailnet, as `lem serve join` keeps it; another name is a `Host` alias of `~/.ssh/config`.
The answer is the board's jump answer, `{"done": ..., "said": ...}`, with a `notice` when agterm
attached the session without all its companions.
"""

from http import HTTPStatus
from typing import TYPE_CHECKING

from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse

from lem.addons.peers import agterm_said, attach_guard, origin_read, registry
from lem.board import listener
from lem.board.acts import jump
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.responses import Response

    from lem.addons.peers.group_said import Shown
    from lem.addons.peers.origin import Origin


def unsure(peer: str, found: Origin, refusal: Refusal) -> Refusal:
    """A session gone on an agterm that did not say whether it runs Live sessions may be one
    outside Live sessions: the refusal says both."""
    if found.live is not None or refusal.code != "peer-session-gone":
        return refusal
    live = agterm_said.not_live(peer)
    return Refusal(
        refusal.code,
        f"{refusal.why}, or the agterm on {peer} does not run Live sessions (it did not say: "
        f"{found.said})",
        f"{refusal.fix}; or {live.fix}",
    )


async def shown(request: Request, joined: registry.Registry) -> Shown:
    """Read the session on the joined board, then show it in this Mac's agterm."""
    peer = request.path_params["peer"]
    session = agterm_said.checked_id(request.path_params["session"])
    found = await origin_read.origin_of(
        joined, (peer, request.path_params["workspace"], session)
    )
    if found.live is False:
        raise agterm_said.not_live(peer)
    guard = attach_guard.guard_of(request)
    try:
        return await run_in_threadpool(
            guard.shown, request.app.state.environ, (peer, peer, session)
        )
    except Refusal as refusal:
        raise unsure(peer, found, refusal) from refusal


def line_of(refusal: Refusal) -> str:
    """What the board says of a refusal: why, then its fix."""
    return f"{refusal.why}; {refusal.fix}."


async def endpoint(request: Request) -> Response:
    """Show the joined machine's session on this Mac, and say what came of it."""
    if listener.at_door(request):
        return jump.answered(jump.DOOR, HTTPStatus.FORBIDDEN, done=False)
    refused = listener.act_refusal(request)
    if refused is not None:
        return jump.answered(refused, HTTPStatus.FORBIDDEN, done=False)
    try:
        seen = await shown(request, registry.held(request))
    except Refusal as refusal:
        return jump.answered(
            line_of(refusal), HTTPStatus.UNPROCESSABLE_ENTITY, done=False
        )
    if seen.notice:
        return JSONResponse({"done": True, "said": seen.said, "notice": seen.notice})
    return jump.answered(seen.said, HTTPStatus.OK, done=True)
