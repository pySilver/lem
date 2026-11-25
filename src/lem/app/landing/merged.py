"""`lem land merged`: the bookkeeping after the forge merged or ended the pull request, and the
task `landed` (`landing.md` B, `merged`; E, "Forge took the call, not merged yet", "Merge taken,
text not updated", "Closed on GitHub", "Base checkout cannot follow").

A merge someone made on GitHub, or the queue that took Lem's call, is written down first, as the
forge shows it; a request closed with no merge drops the task. Then the line of a merge on a
moved base goes into the pull request's text, once: a failed edit keeps the text that waits and
this step stays due. Then the main checkout follows origin's base by a fast-forward only, and a
checkout that cannot follow is left as it is, with git's words. Then the task lands.
"""

from functools import partial
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.landing import (
    changes,
    merge_item,
    merge_step,
    merge_text,
    merge_world,
    merged_beside,
    reconcile,
)
from lem.kernel.errors import Refusal
from lem.model.landing import reconcile as rules
from lem.store import tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.app.landing.frame import Context
    from lem.kernel.envelope import Envelope
    from lem.records.base import Moment
    from lem.records.record import Record

CLOSED = "the pull request was closed on the forge"


def dropped(record: Record, *, line: str, now: Moment) -> Record:
    """The record of a request closed with no merge: the task dropped, nothing of the merge
    waiting."""
    moved = changes.moved(record, "dropped", line, now)
    return changes.landing(moved, intent=None, accepted=None)


def waiting(context: Context) -> Refusal:
    """What an open request shows to `merged`: the queue's end in GitHub's words, written
    down, or that it is not merged yet."""
    dequeued = merge_world.dequeued_of(context)
    found = rules.queued(context.record, context.world, dequeued=dequeued)
    if isinstance(found, Refusal):
        return found
    return reconcile.refused(context, context.record, found)


def adopted(context: Context) -> Record | None:
    """The record with what the forge shows of the request written down: its merge, or its
    close, which drops the task (None: nothing more is done); an open one is refused."""
    record, world = context.record, context.world
    pull = world.pull
    if pull is None or pull.state == "open":
        raise waiting(context)
    if pull.state == "closed":
        line = f"{CLOSED}: {pull.url} is closed with no merge; the branch keeps its commits"
        context.write(record, partial(dropped, line=line, now=world.now))
        return None
    facts = ("owner", "github", merge_world.trees_of(context, pull))
    reconcile.written(
        context, record, rules.landed(record, world, pull, facts), "owner"
    )
    return tasks.read(context.workspace.state, record.task.slug)


def followed(context: Context) -> str | None:
    """Fast-forward the checkout that holds the base, the main one or a linked worktree, to
    origin's base; the line of a checkout that stays. With none, nothing follows."""
    git, checkout = context.ports.git, merge_world.base_checkout(context)
    base = context.world.rules.base
    if checkout is None or git.tip(checkout, "HEAD") == context.world.base:
        return None
    made = git.fast_forward(checkout, f"origin/{base}")
    if isinstance(made, str):
        return None
    return (
        f"{checkout} did not follow origin/{base}, and nothing in it was changed; git said: "
        f"{made.said}"
    )


def finished(record: Record, *, left: str | None, now: Moment) -> Record:
    """The record with the checkout's line, and the task `landed` with the merge's line."""
    merged = record.landing.merged if record.landing else None
    line = "the pull request is merged"
    if merged is not None:
        record = changes.landing(record, merged=replace(merged, left_behind=left))
        line = f"{line}; {merged.uncovered}" if merged.uncovered else line
    return changes.moved(record, "landed", line, now)


def act(context: Context) -> object:
    """Write down what the forge shows, put the merge's line into the pull request's text,
    let the main checkout follow, and land the task."""
    record = context.record
    if record.landing is not None and record.landing.phase in {"open", "preparing"}:
        record = adopted(context)
        if record is None:
            return context.world.pull
    record = merge_text.edited(context, record)
    merge_item.removed(context.workspace, record)
    change = partial(finished, left=followed(context), now=context.world.now)
    record = context.write(record, change)
    return record.landing.merged if record.landing else None


def run(folder: Path, slug: str) -> Envelope:
    """`lem land merged SLUG`."""
    hooks = merge_step.Hooks(admits=merged_beside.admits)
    return merge_step.landed(folder, slug, "merged", act, hooks)
