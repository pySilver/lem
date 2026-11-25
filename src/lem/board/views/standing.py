"""Where a task stands on the board (`board_model.settle` and `STATUS` on `main`): the column of
who acts, its look, who works on it, the words of its state, its icon, whether it moves, and
since when.

A task stands in "Waits for you" while a row of what waits for the owner is his step on it (a
breaker, his wait, a plan, a merge review, a merge, his block, a task after a dropped one); a
card of its session and a session it lacks are rows of his, and the task still stands where its
work is. An ended task is done, a parked one stands apart, a landing and an open pull request
whose merge is not his are in the checks and the review, and every other task builds.
"""

from types import MappingProxyType
from typing import TYPE_CHECKING, Literal

from lem.board.inputs.text import Look
from lem.board.views import rule, stopped
from lem.model.owner import merging, turns
from lem.records.base import Frozen, Moment
from lem.records.holds import Blocked, BreakerHold, OwnerHold, Parked, ReleaseHold

if TYPE_CHECKING:
    from lem.board.views.world import Seen
    from lem.model.owner.looks import Row

type Column = Literal["you", "build", "checks", "done", "parked"]


class Standing(Frozen, frozen=True, kw_only=True):
    """A task's place: its column, its look, who acts, its state's words, its icon, whether
    it moves, and since when (his hold's moment while he holds it, else its status's)."""

    column: Column
    look: Look
    who: str
    label: str
    icon: str
    live: bool = False
    since: Moment


# The rows that make a task his: his step on it, not a card or a session.
YOURS = frozenset(
    (
        "breaker",
        "criteria",
        "held",
        "plan",
        "review",
        "merge",
        "blocked",
        "after_dropped",
    )
)
CHECKS = frozenset(("ready", "landing", "open"))
YOU: Column = "you"
# An open task whose merge is not his: the merge agent reads it, the server merges it, or its
# session lands it again.
MERGE_WAITS = MappingProxyType(
    {
        "reads": rule.Said(
            "gate", "The merge agent", "The merge agent reads it", "eye", live=True
        ),
        "merges": rule.Said("gate", "Lem", "Lem merges it", "code-branch", live=True),
        "relands": rule.Said("gate", "Lem", "Lem lands it again", "play", live=True),
    }
)


def standing(seen: Seen, rows: tuple[Row, ...]) -> Standing:
    """Where the task of `seen` stands, with the rows of what waits for the owner of it."""
    mine = any(row.kind in YOURS for row in rows)
    said = said_of(seen, mine=mine)
    column = column_of(seen, mine=mine)
    if column == YOU and said.look != rule.HELD.look:
        said = rule.Said(
            rule.HELD.look, rule.HELD.who, said.label, said.icon, live=said.live
        )
    return Standing(
        column=column,
        look=said.look,
        who=said.who,
        label=said.label,
        icon=said.icon,
        live=said.live,
        since=since_of(seen),
    )


def column_of(seen: Seen, *, mine: bool) -> Column:
    """The column of who acts on the task."""
    task = seen.record.task
    if mine:
        return YOU
    if task.status in rule.ENDED:
        return "done"
    if isinstance(task.hold, Parked):
        return "parked"
    return "checks" if task.status in CHECKS else "build"


def said_of(seen: Seen, *, mine: bool) -> rule.Said:
    """The words of the task's state: its hold's while one holds it, else its status's."""
    task = seen.record.task
    hold = task.hold
    if task.status in rule.ENDED or hold is None or isinstance(hold, Blocked):
        return status_said(seen)
    if isinstance(hold, Parked):
        return rule.PARKED
    if isinstance(hold, ReleaseHold):
        return rule.BLOCKED
    return rule.HELD if mine else turn_said(seen)


def status_said(seen: Seen) -> rule.Said:
    """The words of the task's status: a block, the merge's wait of an open task, an
    investigation, or the status's own."""
    record = seen.record
    task = record.task
    if isinstance(task.hold, Blocked) and task.status not in rule.ENDED:
        return rule.BLOCKED
    end = stopped.ended(record)
    if end is not None:
        return stopped.ENDS[end.outcome]
    merge = MERGE_WAITS.get(merging.merge_wait(seen.merge_look()) or "")
    if merge is not None:
        return merge
    if rule.investigates(task):
        return rule.INVESTIGATES
    return rule.STATUS[task.status]


def turn_said(seen: Seen) -> rule.Said:
    """The words of a task the owner's hold or a breaker holds while it is not his turn: its
    session works on his answer, Lem goes on without him while the task runs alone, the
    personas read the criteria, or Lem writes them."""
    task = seen.record.task
    session = seen.session
    if session is not None and session.live and session.working:
        return rule.WORKS
    hold = turns.held(task)
    if hold is not None and seen.alone and hold.on in turns.GOES_ON:
        return rule.GOES_ON
    if hold is not None and turns.reading(task, hold.since):
        return rule.READING
    if isinstance(task.hold, BreakerHold):
        return rule.HELD
    return rule.WRITES


def since_of(seen: Seen) -> Moment:
    """Since when the task is where it is: a hold (his, a breaker's, a block, his park) counts
    from its own moment, every other place from the task's status."""
    task = seen.record.task
    if isinstance(task.hold, OwnerHold | BreakerHold | Blocked | Parked):
        return task.hold.since
    return task.since
