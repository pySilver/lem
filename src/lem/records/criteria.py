"""A task's acceptance criteria: each criterion, a change of them with its before and after,
and everything the task knows of them (`criteria.py` on `main`).

The criteria's text is the plan's section, or `criteria.md` on the fast track; the record keeps
what was parsed from it, the approvals, the reads and the change that waits.
"""

from typing import Literal

from lem.records.approvals import Approval, PersonaRead, Size
from lem.records.base import Frozen, Moment
from lem.records.criterion import Criterion
from lem.records.red import Red


class Pair(Frozen, frozen=True, kw_only=True):
    """One criterion's change: changed, removed or added, with its sides as the owner saw
    them."""

    change: Literal["changed", "removed", "added"]
    before: Criterion | None = None
    after: Criterion | None = None


class Change(Frozen, frozen=True, kw_only=True):
    """The owner's change of the criteria: the text he answered, his words, the pairs, and the
    digests before and after. Only the newest is kept whole; `Criteria.changed` keeps the moment
    of each."""

    at: Moment
    text: str
    words: str
    pairs: tuple[Pair, ...] = ()
    before: str
    after: str | None = None


class Waited(Frozen, frozen=True, kw_only=True):
    """The criteria's wait for the owner's yes (`criteria_waited` on `main`): when it began, and
    the approval that ended it, by its number, once one did."""

    since: Moment
    ended_by: int | None = None


class Criteria(Frozen, frozen=True, kw_only=True):
    """What a task knows of its criteria: the size and its reason, the parsed criteria and how
    the change works, the approvals and the newest wait for one, the persona reads, the skip of
    a read and when the owner said yes to it, the change that waits and the moment of each
    change from his notes, and the newest run that the tests pass on the branch and fail on
    the base."""

    size: Size | None = None
    why: str | None = None
    criteria: tuple[Criterion, ...] = ()
    how: str | None = None
    digest: str | None = None
    approvals: tuple[Approval, ...] = ()
    waited: Waited | None = None
    reads: tuple[PersonaRead, ...] = ()
    skip: Literal["asked", "yes", "no"] | None = None
    skip_at: Moment | None = None
    change: Change | None = None
    changed: tuple[Moment, ...] = ()
    red: Red | None = None
