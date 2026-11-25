"""The addresses of the board's pages, its stream and its installed files."""

from starlette.routing import Mount, Route

from lem.board import stream
from lem.board.pages import assets, source

WORKSPACE = "/{host}/{workspace}"
TASK = f"{WORKSPACE}/tasks/{{slug}}"
VIEWS = ("waits", "backlog", "activity", "done", "new")
TABS = (
    "overview",
    "criteria",
    "checks",
    "timeline",
    "artifacts",
    "merge",
    "park",
    "drop",
)

VIEW_ROUTES = tuple(source.route(WORKSPACE, name) for name in VIEWS)
TAB_ROUTES = tuple(source.route(TASK, tab) for tab in TABS)

ROUTES = (
    source.bound("/", "workspaces"),
    Route("/{host}/assets/{path:path}", assets.on_host, name="host-asset"),
    source.bound(f"{WORKSPACE}/", "tasks"),
    Route(f"{WORKSPACE}/stream", stream.endpoint, name="stream"),
    Mount("/assets", app=assets.FILES, name="assets"),
    *VIEW_ROUTES,
    source.bound(TASK, "overview"),
    *TAB_ROUTES,
    source.bound(f"{TASK}/artifacts/{{path:path}}", "artifact"),
    source.bound(f"{TASK}/card/{{page}}", "card"),
)

# After the concrete routes of every table, before the server's general 404.
FALLBACK_ROUTES = (source.bound(f"{TASK}/{{unknown_tab}}", "overview"),)
