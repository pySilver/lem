"""What the landing of a feature sees of its parts: each part as its record reads now, and each
open pull request on the forge whose base is the feature's branch
(`docs/plans/2026-11-27-a-feature-in-parts.md`, "The end").

A feature is a task that a part names in `Task.part_of`; it carries no key of its own. The world
of a task that no record names holds no `Feature`, so that every rule of `feature.py` leaves it
as it was.
"""

from lem.records.base import Frozen, Slug
from lem.records.landing.merge import Merged
from lem.records.landing.record import Pull
from lem.records.landing.review import Reviewed


class PartSeen(Frozen, frozen=True, kw_only=True):
    """One part as its record reads now: its slug and status, its pull request, whether its
    proposal was green, whether it is careful (its proposal's call, from the owner's word, its
    topics or an edit of Lem's settings, or its newest review's call), its newest answered
    review, and its merge into the feature's branch (`Merged.parent` to `Merged.commit`)."""

    slug: Slug
    status: str
    pull: Pull | None = None
    green: bool | None = None
    careful: bool = False
    review: Reviewed | None = None
    merged: Merged | None = None


class Targeting(Frozen, frozen=True, kw_only=True):
    """An open pull request on the forge whose base is the feature's branch: its number, its
    address and its head branch."""

    number: int
    url: str
    head: str


class Feature(Frozen, frozen=True, kw_only=True):
    """The feature's parts, the tasks whose record does not read (one of them may be a part),
    and the open pull requests into the feature's branch, as the forge shows them while the
    feature's own pull request is open."""

    parts: tuple[PartSeen, ...] = ()
    unread: tuple[Slug, ...] = ()
    targeting: tuple[Targeting, ...] = ()
