"""The server's own addresses, the last table of the app: who it is and its stop, the workspaces
as data, a task's raw page and pictures, the board's notifications, and last the addresses that
go to the page they mean (`aliases.py`). A GET answers HEAD with its headers alone."""

from functools import partial

from starlette.routing import Route

from lem.board import aliases, own, taskfiles
from lem.board.push import acts, manifest, reads

TASK = "/{host}/{workspace}/tasks/{slug}"
GET = ("GET",)
POST = ("POST",)

ROUTES = (
    Route("/api/server", own.server, methods=GET),
    Route("/api/server/stop", own.stop, methods=POST),
    Route("/api/workspaces", own.spaces, methods=GET),
    Route("/manifest.webmanifest", manifest.manifest, methods=GET),
    Route("/sw.js", reads.worker, methods=GET),
    Route("/api/push/key", reads.key, methods=GET),
    Route("/api/push/latest", reads.latest, methods=GET),
    Route(
        "/api/push/subscribe",
        partial(acts.answered, work=acts.subscribing),
        methods=POST,
    ),
    Route(
        "/api/push/unsubscribe",
        partial(acts.answered, work=acts.unsubscribing),
        methods=POST,
    ),
    Route("/api/push/test", partial(acts.answered, work=acts.testing), methods=POST),
    Route(f"{TASK}/raw/{{path:path}}", taskfiles.raw, methods=GET),
    Route(f"{TASK}/media/{{path:path}}", taskfiles.media, methods=GET),
    *aliases.ROUTES,
)
