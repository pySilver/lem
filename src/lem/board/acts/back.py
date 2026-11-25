"""Where the page goes after an act: a 303 to the task's page, or to the view it came from, whose
address names the note of the result (`?note=TOKEN`, `board/acts/notes.py`); and the plain
answers of a request that is no act of the board (`serve.Handler.board_act` on `main`).
"""

from http import HTTPStatus
from typing import TYPE_CHECKING
from urllib.parse import quote, urlencode

from starlette.responses import PlainTextResponse, RedirectResponse

from lem.board.acts.notes import NOTES

if TYPE_CHECKING:
    from starlette.requests import Request

    from lem.board.acts.given import Given
    from lem.board.acts.notes import Note

# The views a task's page may stand over (`in`), and the tab a form may come back to.
VIEWS = ("waits", "backlog", "activity", "done")
TAB = "criteria"
NO_FORM = (
    "The request carries no form of the board: form fields of at most a few kilobytes."
)


def base_of(request: Request) -> str:
    """`/HOST/WORKSPACE` of the request's address."""
    host = quote(request.path_params["host"])
    workspace = quote(request.path_params["workspace"])
    return f"/{host}/{workspace}"


def to_task(
    request: Request, slug: str, note: Note, given: Given | None
) -> RedirectResponse:
    """The task's page, on its tab and over its view as the form says, with the note."""
    token = NOTES.put(note)
    return to_token(request, slug, token, given)


def to_token(
    request: Request, slug: str, token: str, given: Given | None
) -> RedirectResponse:
    """The task's page with the note of `token`."""
    query = urlencode(query_of(given, token))
    task = quote(slug, safe="")
    base = base_of(request)
    tab = tab_of(given)
    address = f"{base}/tasks/{task}{tab}?{query}"
    return RedirectResponse(address, status_code=HTTPStatus.SEE_OTHER)


def query_of(given: Given | None, token: str) -> dict[str, str]:
    """The query of the task's page: the view it stands over, when the form names one, and
    the note."""
    if given is None or given.under not in VIEWS:
        return {"note": token}
    return {"in": given.under, "note": token}


def tab_of(given: Given | None) -> str:
    """The tab of the task's page the form came from: the criteria's, or none."""
    if given is None or given.tab != TAB:
        return ""
    return f"/{TAB}"


def to_view(request: Request, view: str, note: Note) -> RedirectResponse:
    """The view `view` of the workspace, with the note."""
    query = urlencode({"note": NOTES.put(note)})
    address = f"{base_of(request)}/{view}?{query}"
    return RedirectResponse(address, status_code=HTTPStatus.SEE_OTHER)


def refused(said: str, status: HTTPStatus = HTTPStatus.FORBIDDEN) -> PlainTextResponse:
    """A request the board takes no act on, and why."""
    return PlainTextResponse(said, status_code=status)
