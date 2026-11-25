"""The ports of a task's command, bound for the workspace of the call (`app/wiring.py`)."""

import os
from typing import TYPE_CHECKING

from lem.app import wiring
from lem.kernel import paths
from lem.ports.place import Place

if TYPE_CHECKING:
    from lem.store.places import Workspace


def bound(where: Workspace) -> wiring.Ports:
    """Every port bound to its first adapter, for the workspace `where`."""
    environ = os.environ
    home = paths.home(environ)
    return wiring.bound(Place(checkout=where.checkout, home=home, environ=environ))
