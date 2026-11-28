"""The HTTP answer to a task's question card."""

from http import HTTPStatus
from typing import TYPE_CHECKING

from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse, Response

from lem.app.asking.overlay_read import PageRefused
from lem.board import listener
from lem.board.acts.asker import asker_of
from lem.board.ask import accept, body, where
from lem.kernel.errors import Refusal
from lem.ports.faults import Unanswered

if TYPE_CHECKING:
    from starlette.requests import Request

    from lem.app.asking.shape import Posted


async def endpoint(request: Request) -> Response:
    """Check the owner's listener and post one answer to the named card."""
    refused = listener.act_refusal(request)
    if refused is not None:
        return said(HTTPStatus.FORBIDDEN, refused)
    posted = await body.read(request)
    if posted is None:
        return said(HTTPStatus.BAD_REQUEST, "The card needs a JSON answer object.")
    asked = await run_in_threadpool(card_of, request)
    if posted.status == "dismissed":
        return Response(status_code=HTTPStatus.NO_CONTENT)
    return await run_in_threadpool(answer, asked, posted)


def card_of(request: Request) -> accept.AtCard:
    """The card address and the listener that received the answer."""
    folder, page, shown = where.located(request)
    return accept.AtCard(
        folder=folder,
        page=page,
        shown=shown,
        who=asker_of(request),
        environ=request.app.state.environ,
        home=request.app.state.home,
    )


def answer(asked: accept.AtCard, posted: Posted) -> Response:
    """Apply the answer off the event loop and give the owner the result."""
    try:
        status, words = accept.accepted(asked, posted)
    except Refusal as error:
        return said(HTTPStatus.CONFLICT, f"{error.why} {error.fix}")
    except (Unanswered, PageRefused) as error:
        return said(
            HTTPStatus.CONFLICT, f"The board cannot confirm the card is open. {error}"
        )
    return said(status, words)


def said(status: HTTPStatus, words: str) -> JSONResponse:
    """The line the card displays in its reply."""
    return JSONResponse({"said": words}, status_code=status)
