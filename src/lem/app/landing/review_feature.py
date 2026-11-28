"""What the review of a feature's end reads beside the brief of any task
(`docs/plans/2026-11-27-a-feature-in-parts.md`, "The end"; `prompts/feature-review.md`).

Each part had its own review, so the feature's review reads in full only what no part's review
read: each commit of the feature's branch since origin's base that is not a part's merge (the
commits from its `Merged.parent` to its `Merged.commit`), and of each merge commit among them (a
sync of origin's base) what it changed beside git's own merge of its parents, which
`git show --remerge-diff` shows and the brief publishes in the task's folder. It lists each
part with its pull request and its review, with the whole diff of each careful part, and the
criteria of the whole feature (`feature_brief.py`). A task that no part names gets none of it.
"""

import shlex
from typing import TYPE_CHECKING

from lem.app.landing.feature_brief import (
    PROMPT,
    CommitRead,
    FeatureRead,
    PartRead,
    SyncRead,
    whole,
)
from lem.kernel import files
from lem.model.landing.feature_said import verdict

if TYPE_CHECKING:
    from lem.app.landing.frame import Context
    from lem.model.landing.feature_seen import Feature, PartSeen
    from lem.ports.git_facts import Commit
    from lem.records.base import Sha

# A merge commit has two parents or more.
MERGE_PARENTS = 2
# The characters of a commit and of a digest that name a published remerge diff.
SHORT = 12


def git_line(context: Context, *words: str) -> str:
    """A command of git in the task's worktree, quoted for the shell."""
    return shlex.join(("git", "-C", str(context.worktree), *words))


def part_read(context: Context, part: PartSeen) -> PartRead:
    """One part as the review lists it, with the command of its whole diff when it is
    careful."""
    pull, merged, careful = part.pull, part.merged, part.careful
    whole = merged is not None and careful
    diff = git_line(context, "diff", merged.parent, merged.commit) if whole else None
    return PartRead(
        slug=part.slug,
        status=part.status,
        pull=pull.number if pull else None,
        url=pull.url if pull else None,
        review=verdict(part),
        careful=careful,
        diff=diff,
    )


def by_parts(context: Context, feature: Feature) -> frozenset[Sha]:
    """The commits of the parts' merges: from each `Merged.parent` to its `Merged.commit`."""
    git, where = context.ports.git, context.worktree
    merges = (part.merged for part in feature.parts if part.merged is not None)
    ranges = (git.commits(where, merged.parent, merged.commit) for merged in merges)
    return frozenset(one.sha for found in ranges for one in found)


def unread(context: Context, feature: Feature) -> tuple[Commit, ...]:
    """The commits of the feature's branch since origin's base that are no part's merge,
    oldest first."""
    world = context.world
    tip = world.tip or world.base
    found = context.ports.git.commits(context.worktree, world.base, tip)
    merged = by_parts(context, feature)
    return tuple(one for one in found if one.sha not in merged)


def sync_read(context: Context, commit: Commit) -> SyncRead:
    """A merge commit, with its remerge diff published in the task's folder when there is
    one."""
    shown = context.ports.git.remerge(context.worktree, commit.sha)
    if not shown:
        return SyncRead(sha=commit.sha, subject=commit.subject)
    body = shown.encode()
    digest = files.digest(body)[:SHORT]
    short = commit.sha[:SHORT]
    named = f"reviews/remerge-{short}-{digest}.diff"
    files.publish(context.folder / named, body)
    return SyncRead(sha=commit.sha, subject=commit.subject, remerge=named)


def commit_read(context: Context, commit: Commit) -> CommitRead:
    """A commit of the feature's own, with the command that shows it whole."""
    shown = git_line(context, "show", commit.sha)
    return CommitRead(sha=commit.sha, subject=commit.subject, show=shown)


def read_of(context: Context) -> FeatureRead | None:
    """What the feature's review reads beside the brief; None for a task that no part
    names."""
    feature = context.world.feature
    if feature is None:
        return None
    commits = unread(context, feature)
    merges = (one for one in commits if len(one.parents) >= MERGE_PARENTS)
    own = (one for one in commits if len(one.parents) < MERGE_PARENTS)
    return FeatureRead(
        prompt=PROMPT,
        parts=tuple(part_read(context, part) for part in feature.parts),
        commits=tuple(commit_read(context, one) for one in own),
        syncs=tuple(sync_read(context, one) for one in merges),
        criteria=whole(context.record.task.criteria),
    )
