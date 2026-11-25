"""The rows of what waits as the board draws them (`board_model.wait_stacks` on `main`): grouped
by task, one entry for each task in the place of its first row, with each of its things in its
order and in the board's words; the rows by their keys, as the phone shows them; and the parked
tasks, which wait for nobody."""

from typing import TYPE_CHECKING

from lem.app.owner import briefs
from lem.app.owner.entries import Keyed, Stacked, Thing
from lem.model.owner import verbs, waiting
from lem.records.holds import Parked

if TYPE_CHECKING:
    from lem.app.owner.entries import Entry
    from lem.app.owner.scope import Scope
    from lem.model.owner.looks import Look, Row, Rows


def stacked(scope: Scope) -> tuple[Stacked, ...]:
    """Each task that waits, with its things."""
    groups = waiting.stacks(scope.rows)
    return tuple(stack_of(group, scope) for group in groups)


def stack_of(group: Rows, scope: Scope) -> Stacked:
    """One task's stack."""
    look = scope.look(group[0].task)
    shown = briefs.brief(look.record)
    return Stacked(
        task=shown.task,
        ask=shown.ask,
        since=shown.since,
        night=shown.night,
        line=shown.line,
        things=tuple(thing_of(row, look) for row in group),
    )


def thing_of(row: Row, look: Look) -> Thing:
    """One thing of a stack, with its verb."""
    record = look.record
    verb = verbs.verb(row, record.task, record.landing)
    return Thing(key=row.key, kind=row.kind, verb=verb)


def keyed(scope: Scope) -> tuple[Keyed, ...]:
    """The rows by their keys, as the phone shows them."""
    return tuple(map(key_of, scope.rows))


def key_of(row: Row) -> Keyed:
    """One row by its key."""
    return Keyed(key=row.key, kind=row.kind, task=row.task)


def parked(scope: Scope) -> tuple[Entry, ...]:
    """The tasks the owner put aside: no row of what waits, and not counted."""
    return tuple(
        briefs.brief(look.record)
        for name, look in scope.looks.items()
        if isinstance(look.record.task.hold, Parked) and scope.slug in {None, name}
    )
