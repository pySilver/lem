"""`lem land merged`: the bookkeeping after the forge's merge, and the task `landed`.

A merge someone made on GitHub is written down first, as the forge shows it. Then the main
checkout follows origin's base by a fast-forward only, and a checkout that cannot follow is left
as it is, with git's words. A queue that took the call, a closed request and the edit of the
pull request's text after the merge are the step `land-merge`'s.
"""

from functools import partial
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.landing import changes, frame, reconcile, step
from lem.kernel.errors import Refusal
from lem.model.landing import reconcile as rules
from lem.model.landing.world import later

if TYPE_CHECKING:
    from pathlib import Path

    from lem.kernel.envelope import Envelope
    from lem.records.base import Moment
    from lem.records.landing.merge import Merged
    from lem.records.record import Record


def adopted(context: frame.Context) -> Record:
    """The record with a merge the forge shows and Lem did not make, written down."""
    record, world = context.record, context.world
    pull = world.pull
    if pull is None or pull.state != "merged":
        raise later(
            "a pull request the forge closed with no merge, or queued", "land-merge"
        )
    found = rules.landed(record, world, pull, ("owner", "github"))
    if isinstance(found, Refusal):
        raise found
    return context.write(record, partial(reconcile.taken, found=found))


def followed(context: frame.Context) -> str | None:
    """Fast-forward the main checkout to origin's base; the line of a checkout that stays."""
    git, checkout = context.ports.git, context.workspace.checkout
    base = context.world.rules.base
    head = git.tip(checkout, "HEAD")
    if head != git.tip(checkout, f"refs/heads/{base}"):
        return f"the main checkout is not on {base}: it stays where it is"
    if head == context.world.base:
        return None
    made = git.fast_forward(checkout, f"origin/{base}")
    return None if isinstance(made, str) else made.said


def finished(record: Record, *, left: str | None, now: Moment) -> Record:
    """The record with the checkout's line, and the task `landed`."""
    merged = record.landing.merged if record.landing else None
    if merged is not None:
        record = changes.landing(record, merged=replace(merged, left_behind=left))
    return changes.moved(record, "landed", "the pull request is merged", now)


def act(context: frame.Context) -> Merged | None:
    """Write down a merge made on GitHub, let the main checkout follow, and land the task."""
    record = context.record
    if record.landing is not None and record.landing.phase == "open":
        record = adopted(context)
    change = partial(finished, left=followed(context), now=context.world.now)
    record = context.write(record, change)
    return record.landing.merged if record.landing else None


def run(folder: Path, slug: str) -> Envelope:
    """`lem land merged SLUG`."""
    return step.landed(folder, slug, "merged", act)
