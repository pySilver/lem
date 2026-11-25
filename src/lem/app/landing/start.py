"""`lem land start`: a round of the landing begins, and the task is `landing`. It has no effect
outside the record: a task whose project names no command of the checks is blocked, and an
open task whose pull request the forge calls conflicting starts its new round with
`--conflicting` whatever step was due."""

from functools import partial
from typing import TYPE_CHECKING

import msgspec

from lem.app.landing import frame, head, review_archive, say, step
from lem.kernel import clock
from lem.kernel.envelope import Envelope
from lem.kernel.errors import Refusal
from lem.model.landing import begin, reconcile, start
from lem.store import places, steps, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.landing.start import Started


def act(context: frame.Context, *, conflicting: bool) -> Started:
    """Record the start of the round, or the block of a task with no command of the checks."""
    record, world = context.record, context.world
    on = head.branch_of(context.worktree) if world.tip else None
    facts = start.Facts(on_branch=on == world.branch)
    started = start.decide(record, world, facts, conflicting=conflicting)
    if isinstance(started, Refusal):
        if started.code == "no-checks" and not begin.is_blocked(record):
            context.write(
                record, partial(begin.blocked, refusal=started, now=world.now)
            )
        raise started
    review_archive.before_start(record, context.folder)
    context.write(record, partial(begin.begun, started=started))
    return started


def called(context: frame.Context) -> bool:
    """Whether the forge calls the task's open pull request conflicting at the proposed head,
    with no merge call on record to reconcile first: a merge intent or an accepted call is
    settled before any new round (`reconcile.pending`)."""
    landing = context.record.landing
    if landing is None or landing.pull is None or landing.proposed is None:
        return False
    if landing.phase != "open" or reconcile.pending(landing, context.world) is not None:
        return False
    pull = context.ports.forge.pull(landing.pull.number)
    return pull.mergeable == "conflicting" and pull.head == landing.proposed.tip


def woken(folder: Path, slug: str) -> Envelope:
    """`lem land start SLUG --conflicting`: the start is due when the forge calls the pull
    request conflicting, else as any step is."""
    workspace = places.workspace(folder)
    tasks.read(workspace.state, slug)
    now = clock.now()
    with steps.step(workspace.state, slug, "start", now):
        context = step.opened(workspace, slug, now)
        if not called(context):
            context = step.allowed(context, "start")
        outcome = msgspec.Raw(msgspec.json.encode(act(context, conflicting=True)))
        following = say.following(slug, step.looked(context))
    return Envelope(ok=True, outcome=outcome, following=following)


def run(folder: Path, slug: str, *, conflicting: bool) -> Envelope:
    """`lem land start SLUG`."""
    if conflicting:
        return woken(folder, slug)
    return step.landed(folder, slug, "start", partial(act, conflicting=False))
