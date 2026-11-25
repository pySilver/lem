"""The hover of a task's line, which says what the line leaves out (the further lines of a
state block on `main`): a breaker's cause, a pull request that is not green, the type of the
request an investigation takes."""

from typing import TYPE_CHECKING

from lem.model.decisions.breaker import CAUSES, KINDS
from lem.records.decisions import Breaker
from lem.records.holds import BreakerHold

if TYPE_CHECKING:
    from lem.records.task import Task


def hover(task: Task, title: str | None = None) -> str | None:
    """What the line leaves out: a breaker's cause, `title` (not green), or the type of the
    request an investigation takes."""
    if isinstance(task.hold, BreakerHold):
        return cause_of(task, task.hold.number)
    if title is not None:
        return title
    found, shape = task.investigation, task.shape
    if found is not None and found.call is None and shape is not None:
        return f"{shape.type}, because {shape.why}"
    return None


def cause_of(task: Task, number: int) -> str | None:
    """Breaker `number`'s cause, with what it stopped."""
    breaker = next(
        (
            one
            for one in task.decisions
            if isinstance(one, Breaker) and one.id == number
        ),
        None,
    )
    if breaker is None:
        return None
    cause = CAUSES[breaker.cause]
    kind = KINDS[breaker.irreversible] if breaker.irreversible else None
    said_cause = f"{cause} ({kind})" if kind else cause
    return f"{breaker.what}: {said_cause}"
