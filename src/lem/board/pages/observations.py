"""One live read of each workspace for its pages and streams."""

from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock
from time import monotonic
from typing import TYPE_CHECKING

from lem.board.pages import workspace

if TYPE_CHECKING:
    from pathlib import Path

    from starlette.requests import Request

    from lem.board.pages.snapshot import Snapshot
    from lem.store.places import Workspace

# The board's base lookup on main:src/lem/serve.py (Workspace.onto_of, REFRESH_SECONDS).
REFRESH_SECONDS = 5.0

# The second field says whether this request made the read, so its page can reuse the files.
type Observation = tuple[Snapshot, bool]


@dataclass
class Reader:
    """The last live read of one workspace, shared under its lock."""

    lock: Lock = field(default_factory=Lock)
    saved: Snapshot | None = None
    at: float = 0

    def read(self, request: Request, space: Workspace) -> Observation:
        """Read the live facts once when the workspace's interval has passed."""
        with self.lock:
            if self.saved is not None and monotonic() - self.at < REFRESH_SECONDS:
                return self.saved, False
            self.saved = workspace.observe(request, space)
            self.at = monotonic()
            return self.saved, True


@dataclass
class Observations:
    """One reader per checkout on this board server."""

    readers: defaultdict[Path, Reader] = field(
        default_factory=lambda: defaultdict(Reader)
    )
    lock: Lock = field(default_factory=Lock)

    def of(self, request: Request, space: Workspace) -> Observation:
        """Share a workspace's read while other workspaces can read independently."""
        with self.lock:
            reader = self.readers[space.checkout]
        return reader.read(request, space)
