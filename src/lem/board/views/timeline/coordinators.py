"""Who holds the time of a build or a landing that no span holds (`add_block`'s coordinator and
`landing` of `time_of` on `main`).

In a build it is the coordinator's: the agent's, or Lem's for the fast track's builder and an
investigation; before its first builder it plans the task, or Lem starts the builder, and after
one it reads the report. In a landing it is Lem's: the rebase before the first step, Lem between
two steps, and Lem after the checks and the review.
"""

from typing import TYPE_CHECKING

from lem.board.views.timeline import shapes

if TYPE_CHECKING:
    from datetime import datetime

    from lem.records.record import Record

    type Covers = list[tuple[datetime, datetime]]

LEAD_SAYS = (shapes.LEAD, "It plans the task", "It reads the builder’s report")
LEM_SAYS = (shapes.LEM, "Lem starts the builder", "Lem reads the report")
REBASE = "The rebase onto the base"
BETWEEN = "Lem, between two steps of the landing"
AFTER = "Lem, after the checks and the review"
NONE_YET = "The landing starts: the rebase onto the base, then its first step"
NO_CHECK = "The landing, with no check on record"


def built(record: Record, inside: Covers, ended: datetime) -> tuple[str, str]:
    """The coordinator of a build, before its first builder or after one."""
    task = record.task
    by_lem = task.lead == "small" or task.investigation is not None
    lane, before, after = LEM_SAYS if by_lem else LEAD_SAYS
    return lane, after if began_before(inside, ended) else before


def began_before(inside: Covers, moment: datetime) -> bool:
    """Whether a stretch of `inside` began before `moment`."""
    first = min((begun for begun, _ in inside), default=None)
    return first is not None and moment > first


def landed(inside: Covers, piece: tuple[datetime, datetime], *, live: bool) -> str:
    """Lem's piece of a landing: before its first step, between two, or after the last."""
    begun, ended = piece
    if not inside:
        return NONE_YET if live else NO_CHECK
    if not began_before(inside, ended):
        return REBASE
    last = max(end for _, end in inside)
    if begun >= last and not live:
        return AFTER
    return BETWEEN
