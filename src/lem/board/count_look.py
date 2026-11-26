"""A board workspace's wait facts without the files the views render."""

import os
from typing import TYPE_CHECKING

from lem.app.owner import looking
from lem.board.duties import context
from lem.board.views.gather import DEMO
from lem.kernel import clock
from lem.settings.board import for_views

if TYPE_CHECKING:
    from pathlib import Path

    from lem.store.places import Workspace


def looked(space: Workspace, home: Path) -> looking.Looked:
    """Read the merge basis and the sessions the workspace's pages count."""
    here = context.bound(space, os.environ, home)
    branch = for_views(space.checkout, home, os.environ).branch
    demo = (space.state / DEMO).is_file()
    return looking.looked(here, clock.now(), branch, demo=demo)
