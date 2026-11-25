"""The boards of another machine of the tailnet, under `/PEER/...` of this one.

Empty until the step `addons-outside` builds the passage: its one address, `/{peer}/{rest}`,
would take every address no other table names, so a stub of it would answer 501 where the board
answers 404. `lem.board.app` imports this table by its fixed path, the one import across the top
row of the layers (the design's part 2).
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from starlette.routing import BaseRoute

ROUTES: tuple[BaseRoute, ...] = ()
