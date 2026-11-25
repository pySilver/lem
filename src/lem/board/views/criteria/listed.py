"""The criteria on their card (`board_task.criteria_rows` and `board_model.plan_criteria_stand`
on `main`): the plan's, with their tests, while they are the contract; else the approved ones as
they stand, with the note that the plan's were not recorded for them.

The plan's criteria are recorded with their tests (or why one has none). They stand while their
texts are the approved ones with each recorded change applied; an approval of other criteria
after them makes the approved ones the contract, which the agent records again.
"""

from typing import TYPE_CHECKING

from lem.board.views.criteria.as_approved import approved_row
from lem.board.views.criteria.checked import criterion_of
from lem.board.views.criteria.tested import ENDED
from lem.model.criteria import digest
from lem.model.decisions.changes import changes_of

if TYPE_CHECKING:
    from lem.board.inputs.task.criteria import Criterion
    from lem.records.record import Record

AGAIN = (
    "approved after the plan’s criteria were recorded: the agent records them again, "
    "with their tests"
)
NOT_AGAIN = (
    "approved after the plan’s criteria were recorded, which were not recorded again"
)
NEVER = "no test of it is on record: the plan’s criteria were never recorded"
NOT_YET = "no test yet: the agent adds its tests in the plan"


def recorded(record: Record) -> bool:
    """Whether the plan's criteria were recorded, each with its tests or why it has none."""
    stated = record.task.criteria.criteria
    return any(one.tests or one.no_test for one in stated)


def stands(record: Record) -> bool:
    """Whether the plan's recorded criteria are the contract: no approval, or the approved
    texts as they stand."""
    expected = changes_of(record.task).expected
    if expected is None:
        return True
    flat = [" ".join(text.split()) for text in expected]
    return digest.flat(record.task.criteria.criteria) == flat


def note_of(record: Record) -> str:
    """The note on each approved criterion that the plan's do not stand for."""
    ended = record.task.status in ENDED
    if recorded(record):
        return NOT_AGAIN if ended else AGAIN
    return NEVER if ended else NOT_YET


def approved_rows(record: Record) -> tuple[Criterion, ...]:
    """The approved criteria as they stand, with the note."""
    expected = changes_of(record.task).expected or ()
    note = note_of(record)
    numbered = enumerate(expected, 1)
    return tuple(approved_row(record, number, text, note) for number, text in numbered)


def criteria_rows(record: Record) -> tuple[Criterion, ...]:
    """The criteria on their card: the plan's while they stand, else the approved ones."""
    if recorded(record) and stands(record):
        return tuple(criterion_of(record, one) for one in record.task.criteria.criteria)
    if record.task.criteria.approvals:
        return approved_rows(record)
    return ()
