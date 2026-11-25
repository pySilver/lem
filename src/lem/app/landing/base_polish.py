"""The polish pass carried through `base`'s rebase (`land.through_rebase` on `main`): its last
commit takes the name of the commit as far from the new tip as it was from the tip before,
while the rebase kept each commit of the change; when git dropped one, the pass runs again."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.app.landing import frame
    from lem.records.base import Sha
    from lem.records.landing.start import Polished


def entry(context: frame.Context) -> Sha | None:
    """The tip the change was at before its rebase: the tip before a conflict a builder
    resolved since, else the tip `base` read."""
    found = (context.record.landing or Landing()).resolution
    if found is not None and found.after == found.before:
        return found.before
    return context.world.tip


def kept_each(context: frame.Context, start: Sha, tip: Sha) -> bool:
    """Whether the rebase from `start` to `tip` kept each commit of the change."""
    git, where, base_now = context.ports.git, context.worktree, context.world.base
    fork = git.merge_base(where, start, tip) or base_now
    return len(git.commits(where, fork, start)) == len(
        git.commits(where, base_now, tip)
    )


def polish(context: frame.Context, tip: Sha, before: Sha | None) -> Polished | None:
    """The polish pass with its last commit by its name on the tip a rebase made: the commit as
    far from the tip as it was from the tip before, while the rebase kept each commit; with no
    last commit when it dropped one or more (the pass runs again). None when it needs no new
    name or is not in the tip before (`land.through_rebase` on `main`); `before` is the tip
    before a rebase a stop cut before its record."""
    git, start = context.ports.git, before or entry(context)
    polished = (context.record.landing or Landing()).polished
    last = polished.after if polished else None
    if polished is None or last is None or start is None or start == tip:
        return None
    if not git.is_ancestor(context.worktree, last, start):
        return None
    if not kept_each(context, start, tip):
        return replace(polished, after=None)
    return replace(polished, after=renamed(context, last, start, tip))


def renamed(context: frame.Context, last: Sha, start: Sha, tip: Sha) -> Sha | None:
    """The commit of `tip` as far from it as `last` is from `start`."""
    git = context.ports.git
    count = len(git.commits(context.worktree, last, start))
    return git.tip(context.worktree, f"{tip}~{count}")
