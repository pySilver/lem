"""The end of one try of a sync: the checks on its merge, and its push with a lease on origin's
branch as the try found it, under the workspace's merge lock (`app/landing/merge_lock.py`), so
that no push of a sync falls between a part's locked read and its merge call. A lease that fails
takes the sync's own merge back, and the sync starts again (`sync.py`)."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.landing import merge_lock
from lem.app.tasks import sync_checks, sync_tip
from lem.records.base import Frozen, Sha
from lem.records.landing.checks import Outcome

if TYPE_CHECKING:
    from lem.app.tasks.sync_frame import Sync
    from lem.ports.git_facts import GitRefused


class Synced(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """A sync that ran: the feature, its branch, the base and the commit of it taken in,
    origin's branch before, the commit the branch holds after, the sync's own merge commit,
    whether it was pushed, and the checks that passed on it."""

    task: str
    branch: str
    base: str
    base_commit: Sha
    before: Sha
    head: Sha
    merge: Sha | None = None
    pushed: bool = False
    checks: tuple[Outcome, ...] = ()


def published(sync: Sync, found: Synced, prior: Sha) -> Synced | None:
    """The checks on the merge and its push; None, with the sync's own merge taken back to
    `prior`, when origin's branch moved under the push."""
    outcomes = sync_checks.checked(sync)
    sent = pushed(sync, found)
    if isinstance(sent, str):
        return replace(found, head=sent, pushed=True, checks=outcomes)
    sync_tip.undone(sync, prior, found.merge)
    return None


def pushed(sync: Sync, found: Synced) -> Sha | GitRefused:
    """The push of the merge with a lease on origin's branch as the try found it, under the
    workspace's merge lock."""
    place = sync.place
    with merge_lock.held(sync_checks.context_of(sync)):
        return sync.git.push(
            place.worktree, place.branch, found.before, commit=found.head
        )
