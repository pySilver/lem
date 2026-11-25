"""The board's Starlette app: five route tables joined by fixed imports, and the server's facts.

Each table is a module of its own step: the pages, the owner's acts, the cards of `lem ask`, the
server's own addresses with the notifications, and the boards of a peer. A step fills its module
and never edits this one. The server holds no truth: every page reads the files at its request.
"""

from typing import TYPE_CHECKING

from starlette.applications import Starlette

from lem.addons.peers import routes as peers
from lem.board import life, shield
from lem.board.acts import routes as acts
from lem.board.ask import routes as ask
from lem.board.pages import routes as pages
from lem.board.push import routes as push
from lem.kernel.errors import Fault

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from lem.board.facts import Facts

ROUTES = (
    *pages.ROUTES,
    *acts.ROUTES,
    *ask.ROUTES,
    *push.ROUTES,
    *peers.ROUTES,
)


def made(
    facts: Facts, *, home: Path, listen: str, stop: Callable[[], None]
) -> Starlette:
    """The app of the server `facts`, for Lem's home folder `home`, listening on `listen`;
    `stop` ends the server after the answer that calls it."""
    app = Starlette(
        routes=list(ROUTES),
        middleware=shield.hosts(listen),
        exception_handlers={Fault: shield.faulted},
        lifespan=life.lifespan(facts, home),
    )
    app.state.facts = facts
    app.state.home = home
    app.state.stop = stop
    return app
