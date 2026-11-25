"""The `Forge` port's first adapter: GitHub through `gh`, run in the main checkout (the design's
part 4).

The port's two parts are two classes (`forge_gh_pulls.py`), joined here. The step `land-propose`
owns this adapter and its contract test; the step `slice-land` built it for the plain path, and
a rebase merge is the step `land-merge`'s.
"""

from typing import TYPE_CHECKING

from lem.adapters.forge_gh_pulls import Pulls, Refs

if TYPE_CHECKING:
    from lem.ports.place import Place


class ForgeGh(Pulls, Refs):
    """The whole port."""


def bind(place: Place) -> ForgeGh:
    """The adapter for `place`: gh in its main checkout, with the command's environment."""
    return ForgeGh(checkout=place.checkout, environ=place.environ)
