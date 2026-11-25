"""The board's Starlette app: five route tables joined by fixed imports, and the server's facts.

Each table is a module of its own step: the boards of a peer, the pages, the owner's acts, the
cards of `lem ask`, and the server's own addresses with the notifications. A step fills its
module and never edits this one. The peers' table comes first, as `serve.Handler.answer` on
`main` looks for a peer before any address of this machine: an address under a peer's name is
that peer's, and its table matches only the names of the peers joined. The server holds no
truth: every page reads the files at its request.
"""

from typing import TYPE_CHECKING

from starlette.applications import Starlette

from lem.addons.peers import routes as peers
from lem.board import life, shield
from lem.board import serving as service
from lem.board.acts import routes as acts
from lem.board.ask import routes as ask
from lem.board.pages import live, provider
from lem.board.pages import routes as pages
from lem.board.push import routes as push

if TYPE_CHECKING:
    from starlette.routing import BaseRoute

    from lem.board.facts import Facts


def routes() -> list[BaseRoute]:
    """The five tables, read when the app is made, the peers' first."""
    return [
        *peers.ROUTES,
        *pages.ROUTES,
        *acts.ROUTES,
        *ask.ROUTES,
        *push.ROUTES,
    ]


def made(facts: Facts, serving: service.Serving) -> Starlette:
    """The app of the server `facts`."""
    watcher = serving.watcher_of(facts.host)
    app = Starlette(
        routes=routes(),
        middleware=shield.shields(facts, serving.listen, serving.door),
        exception_handlers=shield.handlers(),
        lifespan=life.lifespan(facts, serving.home, watcher),
    )
    app.state.page_inputs = provider.inputs
    app.state.act_revision = live.revision
    app.state.facts = facts
    app.state.watcher = watcher
    for name in service.SHARED:
        setattr(app.state, name, getattr(serving, name))
    return app
