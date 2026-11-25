"""What a page asks of a workspace when `gather.py` reads it: who asks, at what minute, at which
version, the place, Lem's home, git's facts, and the terminal's list of sessions."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from lem.app.sessions.listing import Listed
    from lem.board.inputs.layout import Viewer
    from lem.board.views.backlog.ledger import Ledger
    from lem.board.views.branch import Branches
    from lem.board.views.world import Clock, Place


@dataclass(frozen=True, kw_only=True, slots=True)
class Ask:
    """What a page asks of the workspace: who asks, at what minute, at which version, the
    place, Lem's home, git's facts of the tasks' branches and of the backlog (None when git is
    not asked), and the terminal's list of sessions by task (None when it was not asked)."""

    viewer: Viewer
    clock: Clock
    version: str
    place: Place
    home: Path
    git: Branches | None = None
    ledger: Ledger | None = None
    listed: Mapping[str, Listed] | None = None
