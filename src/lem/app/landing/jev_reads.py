"""Jev's reads of each kind in a landing's record."""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.landing import changes
from lem.records.landing.review import JevRead

if TYPE_CHECKING:
    from lem.app.landing.frame import Context
    from lem.records.base import Moment
    from lem.records.record import Record


def of(record: Record) -> tuple[JevRead, ...]:
    """The comparisons and verdicts the task already has."""
    return record.landing.jev if record.landing else ()


def kept_all(context: Context, reads: tuple[JevRead, ...]) -> Record:
    """Write the cache if it changed."""
    if of(context.record) == reads:
        return context.record
    return context.write(context.record, partial(changes.landing, jev=reads))


type Scores = dict[str, float | None]


def scores(reads: list[JevRead], key: str) -> Scores:
    """The saved comparison scores, including items that got no score."""
    matching = (one for one in reads if one.key == key)
    return {one.path: one.score for one in matching if one.path is not None}


def comparisons(
    key: str, scored: Scores, known: Scores, at: Moment
) -> tuple[JevRead, ...]:
    """New comparisons for the finding, one for each item Jev read."""
    return tuple(
        JevRead(key=key, path=path, score=score, at=at)
        for path, score in scored.items()
        if path not in known
    )
