"""One workspace as the local board and its peers list it."""

from lem.records.base import Frozen


class Row(Frozen, frozen=True, kw_only=True):
    """A workspace's displayed facts, apart from any actions."""

    name: str
    path: str = ""
    host: str = ""
    url: str = ""
    waits: int | None = None
    building: int | None = None
    checks: int | None = None
    running: int | None = None
    problem: str | None = None
    reachable: bool | None = None
    answered: int | None = None
    said: str = ""
