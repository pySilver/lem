"""The entries of `lem waiting`, as an agent reads them (`project.cmd_waiting` on `main`).

Every entry names its task, the owner's words of its ask, since when the task is in its status,
the night that opened it, and its line (the wait's own line, else the newest state's); then the
facts of its kind. The rows and the tasks are the board's own "Waits for you", in its order.
"""

from lem.records.base import Day, Frozen, Moment, Sha, Slug
from lem.records.landing.merge import Refused
from lem.records.landing.propose import MergeRead
from lem.records.landing.record import Pull


class Entry(Frozen, frozen=True, kw_only=True):
    """One thing that waits, with its task and the facts of its kind."""

    task: Slug
    ask: str
    since: Moment
    night: Day | None
    line: str | None
    need: str | None = None
    open: str | None = None
    unread: bool | None = None
    page: str | None = None
    prompt: str | None = None
    after: tuple[Slug, ...] | None = None
    start: str | None = None
    drop: str | None = None
    verb: str | None = None
    fix: str | None = None
    why: str | None = None
    tip: Sha | None = None
    pull_request: Pull | None = None
    green: bool | None = None
    not_green: tuple[str, ...] | None = None
    conflict: bool | None = None
    merge_review: MergeRead | None = None
    merge_refused: Refused | None = None


class Thing(Frozen, frozen=True, kw_only=True):
    """One thing of a task in the board's stack: its key, its kind and its verb."""

    key: str
    kind: str
    verb: str


class Stacked(Frozen, frozen=True, kw_only=True):
    """A task of the board's "Waits for you", with each of its things in its order."""

    task: Slug
    ask: str
    since: Moment
    night: Day | None
    line: str | None
    things: tuple[Thing, ...]


class Keyed(Frozen, frozen=True, kw_only=True):
    """A row of the board's "Waits for you" by its key: the rows the phone shows."""

    key: str
    kind: str
    task: Slug
