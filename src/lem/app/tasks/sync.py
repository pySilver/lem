"""`lem task sync NAME`: the feature NAME takes in origin's base while it waits `queued` for its
parts (`docs/plans/2026-11-27-a-feature-in-parts.md`, "The sync").

Under the feature's step lock: its worktree is brought to origin's `feature/NAME` by a
fast-forward, origin's base is merged in by a merge commit, the settings' checks run on the
merge (`sync_checks.py`), and the merge is pushed with a lease on the tip it started from,
under the workspace's merge lock, so that no push of a sync falls between a part's locked read
and its merge call (`sync_push.py`). A part merged meanwhile makes the lease fail: the sync
takes its own merge back and starts again from the fast-forward, TRIES times at most.

A conflict, a red check and a stop leave the merge in the worktree and push nothing; a builder
resolves or repairs it there and runs the sync again, which takes the worktree as it is.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.app.tasks import sync_frame, sync_push, sync_tip
from lem.kernel import clock
from lem.kernel.envelope import Envelope
from lem.model.task import sync_ends
from lem.store import places, steps, tasks

if TYPE_CHECKING:
    from pathlib import Path

# How many times a sync starts again after origin's branch moved under its push: a guess, as
# a part's merge takes minutes and the sync's checks may take as long.
TRIES = 3
# The sync's name on the feature's step lock, which names its command.
STEP = "task sync"


def run(folder: Path, slug: str) -> Envelope:
    """Sync the feature `slug`, and give the envelope with the line for the owner."""
    workspace = places.workspace(folder)
    tasks.read(workspace.state, slug)
    now = clock.now()
    with steps.step(workspace.state, slug, STEP, now):
        sync = sync_frame.opened(workspace, slug, now)
        done = tried(sync)
    return Envelope(
        ok=True,
        outcome=msgspec.Raw(msgspec.json.encode(done)),
        say=sync_ends.said(sync.place, done.head, pushed=done.pushed),
    )


def tried(sync: sync_frame.Sync) -> sync_push.Synced:
    """The sync, started again while origin's branch moves under its push."""
    sync_tip.ready(sync)
    for _ in range(TRIES):
        done = attempt(sync)
        if done is not None:
            return done
    raise sync_ends.moved(sync.place, TRIES)


def attempt(sync: sync_frame.Sync) -> sync_push.Synced | None:
    """One try from the fetch to the push; None when the lease failed."""
    start, base = sync_tip.fetched(sync)
    prior = sync_tip.brought(sync, start)
    merge = sync_tip.merged(sync, prior, base)
    found = sync_push.Synced(
        task=sync.place.slug,
        branch=sync.place.branch,
        base=sync.place.base,
        base_commit=base,
        before=start,
        head=merge or prior,
        merge=merge,
    )
    if found.head == start:
        return found
    return sync_push.published(sync, found, prior)
