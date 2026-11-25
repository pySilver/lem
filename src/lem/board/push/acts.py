"""The board's notifications, turned on or off by a device, or a test push to it: a POST of the
device's subscription as JSON, from the board's own page on this Mac or through the tailnet door
(`Handler.push_act` on `main`). The answer is JSON, with `said` when it is refused.
"""

from http import HTTPStatus
from typing import TYPE_CHECKING

import msgspec

from lem.adapters.notify_push import PushNotifier
from lem.board import listener
from lem.board.push import listing
from lem.board.push.reads import json_of
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from starlette.requests import Request
    from starlette.responses import Response

type Work = Callable[[Request], Awaitable[object]]
# What a device posts, at most, in bytes.
MOST = 4096
NOT_HERE = (
    "The board's notifications are turned on only from the board's own page, on this Mac "
    "or through the tailnet door."
)


class Asked(msgspec.Struct, frozen=True, kw_only=True):
    """A device's ask to let it go, or to test it: its endpoint."""

    endpoint: str


async def given[Form](request: Request, form: type[Form]) -> Form:
    """The request's JSON body in `form`; refused when it is no such object of at most MOST
    bytes, or comes from no page of the board."""
    refused = listener.act_refusal(request)
    if refused is not None:
        raise Refusal("not-here", NOT_HERE, "open the board's own page")
    body = await request.body()
    if not body or len(body) > MOST:
        raise Refusal(
            "no-json", f"the request carries no JSON of at most {MOST} bytes", ""
        )
    try:
        return msgspec.json.decode(body, type=form)
    except (msgspec.DecodeError, RecursionError) as error:
        raise Refusal(
            "no-json", f"the request carries no subscription ({error})", ""
        ) from error


def refused_as(refusal: Refusal) -> Response:
    """The answer of a refused act: 403 from no page of the board, 400 for no JSON, else
    422."""
    codes = {"not-here": HTTPStatus.FORBIDDEN, "no-json": HTTPStatus.BAD_REQUEST}
    status = codes.get(refusal.code, HTTPStatus.UNPROCESSABLE_ENTITY)
    return json_of({"said": refusal.why}, status)


async def answered(request: Request, *, work: Work) -> Response:
    """The answer of an act: what `work` gives as JSON, or its refusal."""
    try:
        outcome = await work(request)
    except Refusal as refusal:
        return refused_as(refusal)
    return json_of(outcome)


async def subscribing(request: Request) -> listing.Switched:
    """Turn the notifications on for the device that posts its subscription."""
    subscription = await given(request, listing.Given)
    agent = request.headers.get("user-agent", "")
    return listing.subscribed(request.app.state.home, subscription, agent)


async def unsubscribing(request: Request) -> listing.Switched:
    """Turn the notifications off for the device of the endpoint posted."""
    asked = await given(request, Asked)
    return listing.unsubscribed(request.app.state.home, asked.endpoint)


async def testing(request: Request) -> object:
    """One test push to the device of the endpoint posted."""
    asked = await given(request, Asked)
    notifier = PushNotifier(request.app.state.home, request.app.state.environ)
    return notifier.tested(asked.endpoint)[0]
