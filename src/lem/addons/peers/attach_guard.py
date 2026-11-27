"""One jump at a time for each session of a joined machine, on one board: a second click while the
first one's steps run waits for them, then finds the row they made and selects it, so agterm
never attaches the session twice (`attaching.py` reads the rows, then attaches).
"""

import threading
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, cast

from lem.addons.peers import attaching

if TYPE_CHECKING:
    from collections.abc import Mapping

    from starlette.requests import Request

    from lem.addons.peers.group_said import Shown

    type Environ = Mapping[str, str]
    # The joined machine, its ssh destination and the session.
    type Target = tuple[str, str, str]


@dataclass
class Guard:
    """A lock for each ssh destination and session, made on its first jump."""

    held: dict[tuple[str, str], threading.Lock] = field(default_factory=dict)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def of(self, host: str, session: str) -> threading.Lock:
        """The lock of the session `session` of `host`."""
        key = (host.lower(), session.upper())
        with self.lock:
            return self.held.setdefault(key, threading.Lock())

    def shown(self, environ: Environ, target: Target) -> Shown:
        """The steps of `attaching.shown` for `(peer, host, session)`, one jump at a time."""
        peer, host, session = target
        with self.of(host, session):
            return attaching.shown(environ, peer, host, session)


def guard_of(request: Request) -> Guard:
    """The guard of the request's board app, made on its first jump."""
    state = request.app.state
    if not hasattr(state, "peer_attach_guard"):
        state.peer_attach_guard = Guard()
    return cast("Guard", state.peer_attach_guard)
