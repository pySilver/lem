"""Give the visible board page its update notice."""

from http import HTTPStatus
from types import MappingProxyType
from typing import TYPE_CHECKING

import msgspec
from starlette.responses import PlainTextResponse, Response

from lem.board import listener, update, update_record

if TYPE_CHECKING:
    from starlette.requests import Request

HEADERS = MappingProxyType({"Cache-Control": "no-store"})


def available(request: Request) -> Response:
    """Whether this release has a notice for a visible board page to take."""
    state = request.app.state
    notice = update_record.read(state.home).pending
    pending = notice is not None and notice.version == state.facts.install.version
    status = HTTPStatus.OK if pending else HTTPStatus.NO_CONTENT
    return Response(status_code=status, headers=HEADERS)


def shown(request: Request) -> Response:
    """A page of the board takes the notice once for this server's release."""
    refused = listener.act_refusal(request)
    if refused is not None:
        return PlainTextResponse(refused, status_code=HTTPStatus.FORBIDDEN)
    state = request.app.state
    notice = update.seen(state.home, state.facts.install.version)
    if notice is None:
        return Response(status_code=HTTPStatus.NO_CONTENT, headers=HEADERS)
    return Response(
        msgspec.json.encode(notice), media_type="application/json", headers=HEADERS
    )
