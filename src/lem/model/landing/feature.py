"""The end of a feature: where its landing differs from a task's
(`docs/plans/2026-11-27-a-feature-in-parts.md`, "The end").

Its `start` waits until every part ended, its `base` takes in origin's base by a merge commit
(`base.py`), it has no polish pass, since each part had its own, and its merge is the owner's
alone, always one squashed commit, refused while an open pull request still goes into its
branch: GitHub moves such a request onto the base once the branch is deleted (section 5). Each
rule takes the world, whose `feature` is None for a task that no part names, and leaves that
task as it was. The words of its refusals and its lines are `feature_said.py`'s.
"""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.task.claim import ENDED

if TYPE_CHECKING:
    from lem.model.landing.feature_seen import Feature, Targeting
    from lem.model.landing.world import World
    from lem.records.record import Record

OWNER = "the request is a feature: the owner merges it, whatever the settings say"
NO_POLISH = "a feature has no polish pass: each of its parts had its own"
# How many pull requests or parts a refusal names, one each; the rest are counted.
NAMED = 10


def squashes(world: World) -> bool:
    """Whether the merge lands the branch as one squashed commit: always for a feature, else
    as `branch.history` says."""
    return world.feature is not None or world.rules.history == "squash"


def unended(feature: Feature) -> tuple[str, ...]:
    """The parts that have not ended, each with its status, then each task whose record does
    not read, which may be a part."""
    left = (part for part in feature.parts if part.status not in ENDED)
    open_parts = tuple(f"{part.slug} ({part.status})" for part in left)
    unread = tuple(f"{slug} (its record does not read)" for slug in feature.unread)
    return (*open_parts, *unread)


def named(lines: tuple[str, ...]) -> str:
    """`lines` joined, the first NAMED of them, and the rest counted."""
    left = len(lines) - NAMED
    rest = f", and {left} more" if left > 0 else ""
    joined = ", ".join(lines[:NAMED])
    return f"{joined}{rest}"


def parts_open(record: Record, world: World) -> Refusal | None:
    """Why the feature's landing may not start: a part of it has not ended, or a task's
    record does not read, which may be one. None for a task that no part names."""
    feature = world.feature
    left = () if feature is None else unended(feature)
    if not left:
        return None
    slug = record.task.slug
    return Refusal(
        "parts-open",
        f"the feature {slug} lands once each of its parts ended, and {named(left)} has "
        "not",
        f"each part lands, or the owner drops it (/lem drop PART); then lem land start {slug} "
        "runs again",
    )


def polish_refusal(record: Record, world: World) -> Refusal | None:
    """Why the polish pass does not run for a feature; None for a task that no part names."""
    if world.feature is None:
        return None
    slug = record.task.slug
    return Refusal("feature", NO_POLISH, f"`lem land checks {slug}` is the next step")


def targeting(record: Record, world: World) -> Refusal | None:
    """Why the feature's merge may not go: an open pull request has its branch as its base.
    After the feature's merge its branch goes, and GitHub moves each such request onto the
    base. None for a task that no part names."""
    found = world.feature.targeting if world.feature else ()
    if not found:
        return None
    branch, base, slug = world.branch, world.rules.base, record.task.slug
    pulls = tuple(map(pull_line, found))
    return Refusal(
        "pulls-into-feature",
        f"{len(pulls)} open pull request(s) go into {branch}: {named(pulls)}. Once the "
        f"feature merges, {branch} goes, and GitHub moves each of them onto {base}",
        f"each of them merges into {branch} first, or its author closes it or moves it to "
        f"another base; then the owner merges {slug}",
    )


def pull_line(pull: Targeting) -> str:
    """An open pull request into the feature's branch, as a refusal names it."""
    return f"#{pull.number} from {pull.head} ({pull.url})"
