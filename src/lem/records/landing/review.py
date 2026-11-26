"""The review before a pull request, its findings, and how each was filed (`landing.md` A,
`Reviewed` and `Filed`)."""

from typing import Literal

from lem.records.base import Frozen, Moment, Sha, TaskPath

# A finding's place against the bar: over it is filed `worth: later`, under it `worth: no`,
# and a cheap one is fixed or a line of the pull request.
type BarPlace = Literal["over", "under", "cheap"]


class Finding(Frozen, frozen=True, kw_only=True):
    """One finding: its id (`r2.3`), level, place, title, the run that shows it, its place
    against the bar and why, and the open backlog item that already holds it."""

    id: str
    level: Literal["must-fix", "should", "nit"]
    where: str
    title: str
    what: str
    against: BarPlace
    why: str | None = None
    open: str | None = None


class Named(Frozen, frozen=True, kw_only=True):
    """A reviewer by its name, and why it ran, was left out or was silent."""

    name: str
    why: str


class Counts(Frozen, frozen=True, kw_only=True):
    """The counts a review agent wrote beside its findings (`prompts/review.md`): must-fix,
    should and nit, and the defects it saw outside the change."""

    must_fix: int = 0
    should: int = 0
    nit: int = 0
    outside: int = 0


class Reviewed(Frozen, frozen=True, kw_only=True):
    """One review attempt, as `read --record` took it: the tip, what it read (the change or a
    conflict's resolution, its scope), the floor and kind, the careful call and why (None for a
    silent attempt, which made none, as `land.cmd_read` on `main` records it), who answered and
    who was silent, the findings, the counts the agent wrote, and which go to `file`."""

    attempt: int
    tip: Sha
    of: Literal["change", "resolution"]
    scope: Literal["resolution", "whole"]
    floor: Literal["read", "round", "full"]
    kind: Literal["read", "round", "full"]
    careful: bool | None = None
    careful_why: str | None = None
    answered: tuple[str, ...] = ()
    silent: tuple[Named, ...] = ()
    ran: tuple[Named, ...] = ()
    left_out: tuple[Named, ...] = ()
    findings: tuple[Finding, ...] = ()
    counts: Counts = Counts()
    to_file: tuple[str, ...] = ()
    review: TaskPath | None = None
    at: Moment


class Jev(Frozen, frozen=True, kw_only=True):
    """Jev's word on a finding: its score over the bar, or why it was not asked."""

    score: float | None = None
    not_asked: str | None = None
    at: Moment


class JevRead(Frozen, frozen=True, kw_only=True):
    """One read of Jev that a landing keeps, so that no finding is sent twice, by this run or
    the next (`alike` and `jev` of `landing.json` on `main`): the finding's key (its digest, or
    the line or item it came from), the item it was asked about (None for a read against the
    bar), Jev's score (None when it gave none), or why it was not asked."""

    key: str
    path: str | None = None
    score: float | None = None
    not_asked: str | None = None
    at: Moment


class Filed(Frozen, frozen=True, kw_only=True):
    """How one finding was filed: an item, the same as an open item, fixed cheaply, or seen; the
    item's path and worth, the older `worth: no` item a new `worth: later` one cites, Jev's
    word, and the commit."""

    finding: str
    disposition: Literal["item", "same", "cheap-fixed", "seen"]
    path: str | None = None
    worth: Literal["later", "no"] | None = None
    cites: str | None = None
    jev: Jev | None = None
    commit: Sha | None = None
    line: str | None = None
