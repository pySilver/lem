"""The ports of a call of `lem decisions`, bound for the workspace at call time."""

import os
from typing import TYPE_CHECKING

from lem.app import wiring
from lem.kernel import paths
from lem.ports.place import Place

if TYPE_CHECKING:
    from pathlib import Path


def ports_of(checkout: Path) -> wiring.Ports:
    """Every port, bound for the workspace of the main checkout `checkout`."""
    environ = os.environ
    place = Place(checkout=checkout, home=paths.home(environ), environ=environ)
    return wiring.bound(place)
