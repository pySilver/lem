"""What the end of a feature says (`feature.py`): the refusals of the merge of origin's base into
its branch, and each part as a line of the pull request's text and of the squash's body, with
its pull request, its status and its review."""

import shlex
from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from lem.model.landing.feature_seen import PartSeen
    from lem.model.landing.world import World
    from lem.records.landing.review import Reviewed
    from lem.records.record import Record

GREEN = MappingProxyType({True: ", green", False: ", not green", None: ""})


def merge_conflict(
    record: Record, world: World, files: tuple[str, ...], where: str
) -> Refusal:
    """The refusal of the merge of origin's base into the feature's branch that stopped on
    files: the merge stays in the worktree for a builder, as a sync's does."""
    slug, onto, branch = record.task.slug, world.rules.base, world.branch
    listed, quoted = ", ".join(files), shlex.quote(where)
    return Refusal(
        "conflict",
        f"the merge of origin/{onto} into {branch} stopped on these file(s): {listed}; the "
        "merge stays in the worktree, and nothing was pushed",
        f"a builder resolves each file in the worktree and commits the merge (`git -C "
        f"{quoted} commit --no-edit`), then lem land base {slug} runs again",
    )


def merge_refused(record: Record, world: World, said: str) -> Refusal:
    """The refusal of the merge of origin's base that git refused with no file in conflict:
    git's words. Nothing is kept for a builder."""
    slug, onto, branch = record.task.slug, world.rules.base, world.branch
    return Refusal(
        "git-refused",
        f"the merge of origin/{onto} into {branch} failed with no file in conflict; git "
        f"said: {said}",
        "nothing is kept for a builder: the owner removes what git names (a hook of git "
        f"that refuses the merge, a lock that another git holds) and lem land base {slug} "
        "runs again",
    )


def verdict(part: PartSeen) -> str:
    """The part's review as a line: its kind and counts, its careful call, and green or
    not; empty with no review on record."""
    review: Reviewed | None = part.review
    if review is None:
        return ""
    counts = review.counts
    tally = f"{counts.must_fix} must-fix, {counts.should} should, {counts.nit} nit"
    careful = "careful" if review.careful else "not careful"
    green = GREEN[part.green]
    return f"review {review.kind}: {tally}, {careful}{green}"


def part_line(part: PartSeen) -> str:
    """One part as the pull request's text and the squash's body list it: its slug, its pull
    request, its status and its review."""
    pull = part.pull
    shown = "no pull request" if pull is None else f"#{pull.number} ({pull.url})"
    review = verdict(part)
    said = f", {review}" if review else ""
    return f"- {part.slug}: {shown}, {part.status}{said}"


def lines(world: World) -> tuple[str, ...]:
    """Each part as a line; none for a task that no part names."""
    feature = world.feature
    if feature is None:
        return ()
    return tuple(map(part_line, feature.parts))
