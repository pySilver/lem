"""Reconcile what waits with the Inbox's receipts and any live replacement sessions."""

from functools import partial
from typing import TYPE_CHECKING

from lem.addons.inbox import client, store
from lem.addons.inbox.delivery import Delivery
from lem.addons.inbox.prepare import prepare
from lem.addons.inbox.snapshot import gather
from lem.app.sessions.waking import wake as wake_task

if TYPE_CHECKING:
    import httpx

    from lem.addons.inbox.records import Record
    from lem.app.owner.looking import Looked
    from lem.app.sessions.here import Here
    from lem.records.base import Moment


def looked(
    called: Here,
    seen: Looked,
    now: Moment,
    link: str,
    http: httpx.Client,
) -> Record:
    """Translate the board's current waits into the Inbox's rules and effects."""
    view = gather(called, seen, now)
    delivery = Delivery(
        state=called.where.state,
        now=now,
        service=client.Inbox(
            opened=view.look.door, cwd=called.where.checkout, http=http
        ),
        wake=partial(wake, called, now),
        prepare=partial(prepare, called, link, view.facts),
        saved=store.read(called.where.state),
    )
    return delivery.run(view.look, view.live)


def wake(called: Here, now: Moment, slug: str) -> bool:
    """Tell a live session to read its Inbox."""
    return wake_task(called, slug, "inbox", None, now).woke
