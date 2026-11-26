"""One Inbox duty for a real workspace and the board URL that reaches it."""

from typing import TYPE_CHECKING

import httpx

from lem.addons.inbox import door, reconcile, store
from lem.app.owner import looking
from lem.app.sessions import here
from lem.kernel import locks
from lem.store import guard

if TYPE_CHECKING:
    from lem.addons.inbox.records import Record
    from lem.records.base import Moment
    from lem.store.places import Workspace


def tick(
    workspace: Workspace,
    now: Moment,
    link: str,
    transport: httpx.BaseTransport | None = None,
) -> Record:
    """Look at a real workspace, with an independent client and a lock for the Inbox effects."""
    called = here.bound(workspace.checkout)
    seen = looking.looked(called, now)
    seen.require_complete()
    saved = store.read(workspace.state)
    if seen.unknown is not None or not (seen.presence.away or saved.entries):
        return saved
    guard.writable(workspace.state)
    with (
        locks.held(workspace.state / store.LOCK),
        httpx.Client(
            transport=transport, timeout=door.SECONDS, trust_env=False
        ) as http,
    ):
        return reconcile.looked(called, seen, now, link, http)
