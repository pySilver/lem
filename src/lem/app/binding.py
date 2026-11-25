"""The one binding of a command's ports: every port bound to its first adapter for the main
checkout of the call's workspace, with Lem's home folder and the environment the command started
with (`app/wiring.py` builds them).

Beside `wiring` rather than in it, which is at its limit of imports.
"""

from typing import TYPE_CHECKING

from lem.app import wiring
from lem.kernel import paths
from lem.ports.place import Place

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path


def bound_for(checkout: Path, environ: Mapping[str, str]) -> wiring.Ports:
    """Every port bound for the main checkout `checkout` and the environment `environ`."""
    home = paths.home(environ)
    return wiring.bound(Place(checkout=checkout, home=home, environ=environ))
