"""`lem decisions criterion`: a change of an approved criterion in the build, written with the
number the record gives it, and the criteria as they stand after it (`decisions.cmd_criterion`
on `main`)."""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.criteria import where
from lem.app.decisions.writing import Change, written
from lem.kernel import clock
from lem.model.decisions import changes, criterion
from lem.records.base import Frozen
from lem.records.decisions import Decision

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record


class Criteria(Frozen, frozen=True, kw_only=True):
    """A criterion's change as recorded, and the criteria as they stand after it."""

    change: Decision
    criteria: tuple[str, ...]


def changing(asked: criterion.Asked, record: Record) -> tuple[Change, Criteria]:
    """The criterion change `asked` for the record as it is, and the criteria it gives."""
    change = partial(criterion.recorded, asked=asked, now=clock.now())
    after = change(record)
    made = after.task.decisions[-1]
    expected = changes.changes_of(after.task).expected or ()
    return change, Criteria(change=made, criteria=expected)


def recorded(folder: Path, slug: str, asked: criterion.Asked) -> Criteria:
    """`lem decisions criterion SLUG ...`: the change, and the criteria it gives."""
    here = where.here_of(folder, slug)
    return written(here.workspace.state, slug, partial(changing, asked))
