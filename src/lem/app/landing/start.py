"""`lem land start`: the landing of a ready task begins, and the task is `landing`. It has no
effect outside the record."""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.landing import changes, frame, step
from lem.kernel.errors import Refusal
from lem.model.landing import start

if TYPE_CHECKING:
    from pathlib import Path

    from lem.kernel.envelope import Envelope
    from lem.records.landing.start import Started
    from lem.records.record import Record


def act(context: frame.Context, *, conflicting: bool) -> Started:
    """Record the start of the round, keeping what the landing holds already."""
    started = start.decide(context.record, context.world, conflicting=conflicting)
    if isinstance(started, Refusal):
        raise started
    context.write(context.record, partial(begun, started=started))
    return started


def begun(record: Record, *, started: Started) -> Record:
    """The record with the round started, and the task `landing`."""
    changed = changes.landing(record, started=started)
    return changes.moved(changed, "landing", "the landing starts", started.at)


def run(folder: Path, slug: str, *, conflicting: bool) -> Envelope:
    """`lem land start SLUG`."""
    return step.landed(folder, slug, "start", partial(act, conflicting=conflicting))
