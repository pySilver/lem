"""What every act goes through (`serve.Handler.board_act` on `main`): the main listener's check of
where it came from, the workspace of its address and its form; then, for an act on a task, the
act itself in a worker thread, and a 303 to the task's page with the note of what came of it.

The server holds no truth: each act reads the records as they are when it runs.
"""

from http import HTTPStatus
from typing import TYPE_CHECKING

from starlette.concurrency import run_in_threadpool

from lem.board import listener
from lem.board.acts import asker, back, given
from lem.board.acts.asked import Asked
from lem.board.pages import place
from lem.kernel import clock

if TYPE_CHECKING:
    from collections.abc import Callable

    from starlette.requests import Request
    from starlette.responses import Response

    from lem.board.acts.notes import Note

type Act = Callable[[Asked], Note]


async def asked_of(request: Request) -> Asked | Response:
    """The act the request asks, or the answer of a request that is no act of the board's."""
    said = listener.act_refusal(request)
    if said is not None:
        return back.refused(said)
    space = place.workspace(request)
    form = await given.given(request)
    if form is None:
        return back.refused(back.NO_FORM, HTTPStatus.BAD_REQUEST)
    slug = request.path_params.get("slug", "")
    who = asker.asker_of(request)
    return Asked(
        checkout=space.checkout, slug=slug, given=form, asker=who, now=clock.now()
    )


async def on_task(request: Request, act: Act) -> Response:
    """Run `act` on the task of the address, and go to its page with the note."""
    asked = await asked_of(request)
    if not isinstance(asked, Asked):
        return asked
    note = await run_in_threadpool(act, asked)
    return back.to_task(request, asked.slug, note, asked.given)
