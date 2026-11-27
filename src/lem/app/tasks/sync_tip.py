"""The git of a sync of a feature: its worktree checked, origin fetched, the worktree brought to
origin's branch by a fast-forward, origin's base merged in by a merge commit (never a rebase,
which drops the merge commits of the parts and of earlier syncs), and the sync's own merge
taken back when origin's branch moved under its push.

A worktree that holds commits origin's branch lacks (a builder's resolution of a conflict, or a
merge whose checks a builder repaired) is taken as it is, while it holds origin's branch.
"""

from typing import TYPE_CHECKING

from lem.app.tasks import remote
from lem.model.landing import destination
from lem.model.task import sync as rules
from lem.model.task import sync_ends, sync_stops
from lem.ports.git_facts import Conflict, GitRefused

if TYPE_CHECKING:
    from lem.app.tasks.sync_frame import Sync
    from lem.records.base import Sha


def ready(sync: Sync) -> None:
    """Refuse a worktree that is not there, is on another branch, or holds changes that no
    commit holds (a merge that stopped among them)."""
    place, git = sync.place, sync.git
    if not (place.worktree / ".git").exists():
        raise sync_stops.no_worktree(place)
    on = git.branch_of(place.worktree)
    if on != place.branch:
        raise sync_stops.off_branch(place, on)
    if not git.clean(place.worktree, untracked=False):
        raise sync_stops.dirty(place)


def fetched(sync: Sync) -> tuple[Sha, Sha]:
    """Origin's branch of the feature and origin's base, after a fetch."""
    place, git = sync.place, sync.git
    said = remote.fetch_warning(git, sync.checkout)
    if said is not None:
        raise sync_ends.unfetched(place, said)
    start = git.remote_head(sync.checkout, place.branch)
    if start is None:
        raise destination.missing(place.branch)
    base = git.remote_head(sync.checkout, place.base)
    if base is None:
        raise destination.missing(place.base)
    return start, base


def brought(sync: Sync, start: Sha) -> Sha:
    """The worktree's tip once it holds origin's branch at `start`: as it is when it holds it,
    else fast-forwarded; refused when the two went apart."""
    place, git = sync.place, sync.git
    head = git.tip(place.worktree, "HEAD") or ""
    if head and git.is_ancestor(place.worktree, start, head):
        return head
    if head and not git.is_ancestor(place.worktree, head, start):
        raise sync_stops.diverged(place)
    made = git.fast_forward(place.worktree, f"origin/{place.branch}")
    if isinstance(made, GitRefused):
        raise sync_stops.refused(place, "fast-forward", made.said)
    return made


def merged(sync: Sync, head: Sha, base: Sha) -> Sha | None:
    """The merge commit of origin's base into the worktree's branch; None when the tip holds
    the base already. A conflict stays in the worktree for a builder."""
    place, git = sync.place, sync.git
    if git.is_ancestor(place.worktree, base, head):
        return None
    message = rules.message(place.base, place.branch)
    made = git.merge(place.worktree, base, message)
    if isinstance(made, Conflict):
        raise sync_stops.conflict(place, made.files)
    if isinstance(made, GitRefused):
        raise sync_stops.refused(place, "merge", made.said)
    return made


def undone(sync: Sync, prior: Sha, merge: Sha | None) -> None:
    """After a push whose lease failed: the sync's own merge taken back to `prior`, so that
    the worktree comes up to origin's branch again by a fast-forward. Commits of a builder
    stay, and the next fetch finds the two apart."""
    if merge is None:
        return
    place = sync.place
    back = sync.git.reset(place.worktree, prior, merge)
    if isinstance(back, GitRefused):
        raise sync_stops.refused(place, "reset", back.said)
