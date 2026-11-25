"""An approved criterion as it stands, on the card of the criteria while the plan's do not stand
for it (`board_task.criteria_rows` on `main`): its sentence, the steps of its case, its chart,
and the note that its tests are not recorded."""

from typing import TYPE_CHECKING

from lem.board.inputs.task.criteria import Case, Criterion
from lem.board.views.criteria.checked import charted
from lem.model.criteria import digest

if TYPE_CHECKING:
    from lem.records.criterion import Criterion as Stated
    from lem.records.record import Record


def approved_row(record: Record, number: int, text: str, note: str) -> Criterion:
    """An approved criterion: its sentence, the steps of its case, its chart, the note."""
    first, *steps = text.split("\n")
    return Criterion(
        id=f"criterion-{number}",
        number=number,
        look="quiet",
        icon="file-lines",
        text=first,
        cases=(Case(steps=tuple(steps)),) if steps else (),
        chart=charted(record, number, chart_of(record, text)),
        note=note,
    )


def chart_of(record: Record, text: str) -> str | None:
    """The chart of the approved criterion of this whole text; none for one a change
    wrote."""
    newest = record.task.criteria.approvals[-1]
    same = (one.chart for one in newest.criteria if same_text(one, text))
    return next(same, None)


def same_text(stated: Stated, text: str) -> bool:
    """Whether a criterion's whole text is `text`, each run of spaces as one."""
    return digest.same(digest.whole(stated), text)
