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
    digests before and after. Only the newest is kept."""

    at: Moment
    text: str
    words: str
    pairs: tuple[Pair, ...] = ()
    before: str
    after: str | None = None


class Criteria(Frozen, frozen=True, kw_only=True):
    """What a task knows of its criteria: the size and its reason, the parsed criteria and how
    the change works, the approvals, the persona reads, the skip of a read, the change that
    waits, and the newest run that the tests pass on the branch and fail on the base."""

    size: Size | None = None
    why: str | None = None
    criteria: tuple[Criterion, ...] = ()
    how: str | None = None
    digest: str | None = None
    approvals: tuple[Approval, ...] = ()
    reads: tuple[PersonaRead, ...] = ()
    skip: Literal["asked", "yes", "no"] | None = None
    change: Change | None = None
    red: Red | None = None
