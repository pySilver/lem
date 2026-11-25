"""The criteria that wait for the owner's yes, first on the tab (`board_task.approve_card` on
`main`): as the task's session wrote them (`criteria.md` of its folder), with the personas' read
in one line, the change from his note above them, and his answer under them on a page that may
act, a sheet a phone reads to its end first. It is there while a row of what waits for him is
the criteria's (`owed.py`), and, once he answered on the board, it says his answer is on record
until the task's session takes it.

The task gets a question when its wait begins. The form carries the mark of the file this page
read, and it is offered only while that mark agrees with a mark on record.
"""

from typing import TYPE_CHECKING

from lem.board.inputs.task.criteria import Approve
from lem.board.views import owed
from lem.board.views.criteria import asking, reading
from lem.board.views.criteria.change import change_of
from lem.board.views.criteria.sheet import back, written
from lem.model.criteria import waits
from lem.model.owner import answers

if TYPE_CHECKING:
    from lem.board.views.world import Seen, World

UNWRITTEN = (
    "The task’s session writes them to criteria.md in the task directory, and the board "
    "shows them here then. Until then, approve them in the task’s session."
)
ELSEWHERE = (
    "Approve them in the task’s session, or on this board on the Mac or through the "
    "tailnet door."
)


def approve(world: World, seen: Seen) -> Approve | None:
    """The card of the criteria's wait, or None while they wait for no yes of his."""
    task = seen.record.task
    hold = waits.hold_of(task)
    if hold is None:
        return None
    question = waits.question_of(task)
    if answers.answered_hold(task, hold) and question is not None:
        return card(world, seen, took=asking.took_of(world, question))
    rows = owed.of_task(world, task.slug)
    if not any(row.kind == "criteria" for row in rows):
        return None
    return card(world, seen)


def card(world: World, seen: Seen, took: str | None = None) -> Approve:
    """The card, with his answer on record, his answer form, or the words where the page
    may not act."""
    task = seen.record.task
    text = seen.text(asking.WAITING)
    question = asking.shown_question(task, text)
    acts = took is None and world.viewer.may_act and question is not None
    form = asking.form_of(world, task, question) if acts and question else None
    return Approve(
        label="Approve the criterion" if asking.fast(task) else "Approve the criteria",
        head="The criteria wait for your yes",
        read=reading.read_line(task),
        change=None if text is None else change_of(task),
        criteria=written(world, seen, text),
        plain=text if form else None,
        answer=form,
        back=back(world, seen) if form else None,
        took=took,
        words=words_of(text, took=took, acts=bool(form)),
        sheet=form is not None,
    )


def words_of(text: str | None, *, took: str | None, acts: bool) -> str | None:
    """Where the owner approves them when the card holds no form."""
    if took is not None or acts:
        return None
    return UNWRITTEN if text is None else ELSEWHERE
