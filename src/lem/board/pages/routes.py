"""The board's pages, its stream and its assets.

The kanban of a workspace, its stream and the files under `/assets/` are built (the slice of
`slice-board`); every other page answers 501 until the step `board-pages` builds it.
"""

from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from lem.board import stream, stub
from lem.board.pages import kanban
from lem.kernel import paths

WORKSPACE = "/{host}/{workspace}"
TASK = f"{WORKSPACE}/tasks/{{slug}}"
ASSETS = paths.root() / "skills" / "lem" / "assets"

ROUTES = (
    Route(f"{WORKSPACE}/", kanban.page, methods=["GET"]),
    Route(f"{WORKSPACE}/stream", stream.endpoint, methods=["GET"]),
    Mount("/assets", app=StaticFiles(directory=ASSETS), name="assets"),
    *stub.routes(
        "board-pages",
        "GET",
        "/",
        "/{host}/assets/{path:path}",
        f"{WORKSPACE}/waits",
        f"{WORKSPACE}/backlog",
        f"{WORKSPACE}/activity",
        f"{WORKSPACE}/done",
        f"{WORKSPACE}/new",
        TASK,
        f"{TASK}/overview",
        f"{TASK}/criteria",
        f"{TASK}/checks",
        f"{TASK}/timeline",
        f"{TASK}/artifacts",
        f"{TASK}/artifacts/{{path:path}}",
        f"{TASK}/card/{{page}}",
        f"{TASK}/merge",
        f"{TASK}/park",
        f"{TASK}/drop",
    ),
)
