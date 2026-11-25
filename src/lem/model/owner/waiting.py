"""The one list of what waits for the owner (`board_model.waits_of`, `wait_stacks` and
`wait_count` on `main`): one row for each thing he does, the most pressing first, and the same
rows grouped by task.

A task two releases back has one row, the stop's, and nothing else of it is his until the drop.
A stop the guard logged, or a session the task lacks, comes first; then a breaker, his wait in
his turn, a task queued after a dropped one, his block, each open card; a plan to read; a merge
review that calls him; and a pull request whose merge waits for him. Rows of one kind keep the
order of their moments. A task counts once, however many of its things wait.
"""

from itertools import chain
from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.model.owner import held, merges, need
from lem.model.owner.looks import Row
from lem.records.holds import Parked, ReleaseHold

if TYPE_CHECKING:
    from collections.abc import Mapping

    from lem.model.owner.looks import Look, Looks, Rows
    from lem.records.base import Moment
    from lem.records.task import Task

ENDED = need.ENDED
# The order of the kinds: what stops a task first, a merge review before its merge.
ORDER = MappingProxyType(
    {
        "breaker": 0,
        "session": 0,
        "stopped": 0,
        "criteria": 1,
        "held": 1,
        "card": 1,
        "after_dropped": 1,
        "blocked": 1,
        "plan": 2,
        "review": 3,
        "merge": 4,
    }
)


def rows(looks: Looks, *, away: bool, now: Moment) -> Rows:
    """Every row of what waits for the owner, in the list's order."""
    tasks = {look.record.task.slug: look.record.task for look in looks}
    each = (rows_of(look, tasks, away=away, now=now) for look in looks)
    return tuple(sorted(chain.from_iterable(each), key=order_of))


def order_of(row: Row) -> tuple[int, Moment]:
    """The place of a row: its kind's, then its moment."""
    return ORDER[row.kind], row.since


def rows_of(look: Look, tasks: Mapping[str, Task], *, away: bool, now: Moment) -> Rows:
    """The rows of one task."""
    task = look.record.task
    hold = task.hold
    if isinstance(hold, ReleaseHold) and task.status not in ENDED:
        return (released_row(task.slug, hold),)
    first = need.session_rows(look, tasks, now)
    if task.status in ENDED or isinstance(hold, Parked):
        return first
    alone = away or task.night is not None
    return first + going_rows(look, tasks, alone=alone)


def going_rows(look: Look, tasks: Mapping[str, Task], *, alone: bool) -> Rows:
    """The rows of a task that did not end and is not parked, beside its session's."""
    asked = held.hold_rows(look, alone=alone) + held.after_rows(look, tasks)
    shown = held.blocked_rows(look) + held.card_rows(look)
    return asked + shown + merges.merge_rows(look)


def released_row(slug: str, hold: ReleaseHold) -> Row:
    """The one row of a task two releases back: the stop's message."""
    key = f"blocked:{slug}"
    return Row(
        kind="blocked",
        key=key,
        task=slug,
        since=hold.since,
        say=hold.say,
    )


def stacks(found: Rows) -> tuple[Rows, ...]:
    """The rows grouped by task, each group in the place of its first row and its rows in
    their order: a group of one row is that row, of two or more one stack that opens."""
    order: dict[str, list[Row]] = {}
    for row in found:
        order.setdefault(row.task, []).append(row)
    return tuple(tuple(group) for group in order.values())
