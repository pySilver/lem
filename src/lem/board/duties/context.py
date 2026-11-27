"""What one duty works with at one tick: the workspace's name on the board, the workspace with
its ports bound for this tick, the moment, and what the server keeps of it between ticks.

The ports are bound as a command's are (`app/binding.py`), with the server's environment: an
act of a duty calls the same `app` function as the command of its name, in this process.
"""

import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

from lem.app import binding
from lem.app.sessions.here import Here

if TYPE_CHECKING:
    from collections.abc import Mapping
    from datetime import datetime
    from pathlib import Path

    from lem.board.duties.memory import Kept
    from lem.store.places import Workspace


@dataclass(frozen=True, kw_only=True, slots=True)
class Duty:
    """One workspace at one tick."""

    name: str
    here: Here
    now: datetime
    kept: Kept

    @property
    def checkout(self) -> Path:
        """The workspace's main checkout."""
        return self.here.where.checkout

    @property
    def state(self) -> Path:
        """The workspace's state folder."""
        return self.here.where.state

    def say(self, line: str) -> None:
        """One line in the server's log, with the workspace's name."""
        said(self.name, line)


def said(name: str, line: str) -> None:
    """One line in the server's log, with the name of its workspace `name`."""
    sys.stderr.write(f"lem serve: {name}: {line}\n")


def bound(space: Workspace, environ: Mapping[str, str], home: Path) -> Here:
    """The workspace `space` with its ports bound for the server's environment and Lem's home
    folder `home`."""
    ports = binding.bound_for(space.checkout, environ)
    return Here(where=space, ports=ports, caller=None, home=home)
