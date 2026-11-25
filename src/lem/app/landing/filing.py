"""`lem land file`: each finding of the newest review gets its place. The plain path records a
finding under the bar as seen, with no file and no commit; an item of the backlog and the words
`--same`, `--new` and `--again` are the step `land-review`'s."""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.landing import changes, frame, step
from lem.kernel.errors import Refusal
from lem.model.landing import filing
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from pathlib import Path

    from lem.kernel.envelope import Envelope
    from lem.records.landing.review import Filed
    from lem.records.record import Record


def filed(record: Record, *, places: tuple[Filed, ...]) -> Record:
    """The record with the findings' places."""
    landing = record.landing or Landing()
    return changes.landing(record, filed=(*landing.filed, *places))


def act(context: frame.Context) -> tuple[Filed, ...]:
    """Give each finding that waits its place, and record them."""
    places = filing.decide(context.record, context.world)
    if isinstance(places, Refusal):
        raise places
    context.write(context.record, partial(filed, places=places))
    return places


def run(folder: Path, slug: str) -> Envelope:
    """`lem land file SLUG`."""
    return step.landed(folder, slug, "file", act)
