"""The `Notifier` port: a wait for the owner that began, and one that ended (the design's part
4). Web Push, the terminal's mark and the Inbox add-on each take it.

A wait's id names what waits and the moment its question was asked (`breaker:SLUG:N:STAMP`,
`merge:SLUG`), so a wait asked again is a new one (`push.py` on `main`).
"""

from typing import Protocol

from lem.records.base import Frozen, Moment, Slug


class Wait(Frozen, frozen=True, kw_only=True):
    """A wait for the owner: its id and kind, the task and workspace, the line he reads, the
    page that answers it, and since when."""

    id: str
    kind: str
    task: Slug
    workspace: str
    say: str
    url: str
    since: Moment


class Notifier(Protocol):
    """Tell the owner a wait began, or ended."""

    def started(self, wait: Wait) -> None: ...
    def ended(self, wait_id: str) -> None: ...
