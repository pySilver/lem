"""The part of a review's brief that only a feature's end has (`review_feature.py` fills it;
`prompts/feature-review.md` says how its review reads it): the prompt, the parts, the commits
that no part's review read, the syncs of origin's base, and the criteria of the whole feature.
"""

from typing import TYPE_CHECKING

from lem.records.base import Frozen, Sha, Slug, TaskPath

if TYPE_CHECKING:
    from lem.records.criteria import Criteria

PROMPT = "prompts/feature-review.md"


class PartRead(Frozen, frozen=True, kw_only=True):
    """One part as the review lists it: its slug and status, its pull request, its review as
    a line, its careful call, and for a careful part the command that shows its whole diff."""

    slug: Slug
    status: str
    pull: int | None = None
    url: str | None = None
    review: str = ""
    careful: bool = False
    diff: str | None = None


class CommitRead(Frozen, frozen=True, kw_only=True):
    """A commit of the feature's branch that no part's review read: its sha, its subject, and
    the command that shows it whole."""

    sha: Sha
    subject: str
    show: str


class SyncRead(Frozen, frozen=True, kw_only=True):
    """A merge commit of origin's base into the feature's branch: its sha, its subject, and
    the file in the task's folder with what it changed beside git's own merge of its parents;
    None when git made the merge alone, which leaves nothing to read."""

    sha: Sha
    subject: str
    remerge: TaskPath | None = None


class CriterionRead(Frozen, frozen=True, kw_only=True):
    """A criterion of the whole feature: its number and its sentence."""

    number: int
    text: str


class FeatureRead(Frozen, frozen=True, kw_only=True):
    """What the feature's review reads beside the brief of any task: the prompt it follows,
    the parts, the commits no part's review read, the syncs, and the criteria of the whole
    feature. The prompt has no default, so that the published brief always names it."""

    prompt: str
    parts: tuple[PartRead, ...] = ()
    commits: tuple[CommitRead, ...] = ()
    syncs: tuple[SyncRead, ...] = ()
    criteria: tuple[CriterionRead, ...] = ()


def whole(criteria: Criteria) -> tuple[CriterionRead, ...]:
    """The criteria of the whole feature: each one of no part."""
    found = (one for one in criteria.criteria if one.part is None)
    return tuple(CriterionRead(number=one.number, text=one.text) for one in found)
