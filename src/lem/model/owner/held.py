"""The rows of a task that did not end, beside its session and its merge
(`board_model.held_row` and `waits_of` on `main`): a breaker that waits, the owner's wait in his
turn, a task queued after a dropped one, a block that is his, and each open card of its live
session.

A breaker is one row, and the hold it set is not a second. His wait is a row while it is his turn
and his answer on the board is not on record for the session to take. A block that waits for
the task repairing the base is that task's, not his.
"""

from typing import TYPE_CHECKING

from lem.model.owner import answers, turns
from lem.model.owner.looks import Row
from lem.model.task import breaker_question, feature_parts
from lem.records.holds import Blocked, BreakerHold, OwnerHold

if TYPE_CHECKING:
    from collections.abc import Mapping

    from lem.model.owner.looks import Kind, Look
    from lem.records.task import Task

PLAN: Kind = "plan"


def hold_rows(look: Look, *, alone: bool) -> tuple[Row, ...]:
    """The row of the task's breaker or of the owner's wait in his turn, or none."""
    session = look.session
    working = session is not None and session.live and session.working
    task = look.record.task
    hold = task.hold
    if isinstance(hold, BreakerHold):
        return () if working else breaker_rows(task, hold)
    if not isinstance(hold, OwnerHold) or not turns.his_turn(task, alone=alone):
        return ()
    kind = kind_of(task, hold)
    if (working and kind != PLAN) or answers.answered_hold(task, hold):
        return ()
    return (
        Row(
            kind=kind,
            key=key_of(kind, task.slug),
            task=task.slug,
            since=hold.since,
        ),
    )


def breaker_rows(task: Task, hold: BreakerHold) -> tuple[Row, ...]:
    """The breaker's row, while his answer on the board waits for no session."""
    if answers.taken_by_session(breaker_question.current(task, hold)):
        return ()
    key = f"breaker:{task.slug}:{hold.number}"
    return (Row(kind="breaker", key=key, task=task.slug, since=hold.since),)


def key_of(kind: Kind, slug: str) -> str:
    """The key of his wait's row: a plan's is its own, every other the held task's."""
    prefix = PLAN if kind == PLAN else "held"
    return f"{prefix}:{slug}"


def kind_of(task: Task, hold: OwnerHold) -> Kind:
    """The kind of row of his wait: the criteria that wait for his yes (also an interview's
    once its questions ended), a plan to read, or another step of his."""
    questions_ended = hold.on == "interview" and turns.asked(task) is not None
    if hold.on == "criteria" or questions_ended:
        return "criteria"
    if hold.on == PLAN and task.status == "planned":
        return PLAN
    return "held"


def after_rows(look: Look, tasks: Mapping[str, Task]) -> tuple[Row, ...]:
    """One row of a queued task, with each dropped task it waits for."""
    task = look.record.task
    if task.status != "queued":
        return ()
    dropped = feature_parts.dropped_before(task, tasks)
    if not dropped:
        return ()
    key = f"after_dropped:{task.slug}"
    row = Row(
        kind="after_dropped",
        key=key,
        task=task.slug,
        since=max(task.since, dropped[0].since),
        after=tuple(one.slug for one in dropped),
    )
    return (row,)


def blocked_rows(look: Look) -> tuple[Row, ...]:
    """The row of a block that is the owner's: not one that waits for another task."""
    task = look.record.task
    hold = task.hold
    if not isinstance(hold, Blocked) or hold.after is not None:
        return ()
    key = f"blocked:{task.slug}"
    return (Row(kind="blocked", key=key, task=task.slug, since=hold.since),)


def card_rows(look: Look) -> tuple[Row, ...]:
    """Each open card of the task's live session, oldest first."""
    task, session = look.record.task, look.session
    if session is None or not session.live:
        return ()
    return tuple(
        Row(
            kind="card",
            key=f"card:{task.slug}:{one.id}",
            task=task.slug,
            since=one.asked,
            card=one.id,
            prompt=one.question,
        )
        for one in task.questions
        if one.topic == "card" and one.answer is None and one.id in session.cards
    )
