"""The kanban of a workspace from its task records: a pure view (the slice of `slice-board`;
`board-views` owns the lanes' rule, which today also reads who acts and what waits).

A task the owner's answer or a breaker holds waits for him; one that is ready, landing or open
is in the checks and the review; an ended one is done, the newest first; every other one builds.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.board.inputs.kanban import Card, Kanban, Lane
from lem.kernel import clock
from lem.records.holds import BreakerHold, OwnerHold

if TYPE_CHECKING:
    from lem.records.record import Record
    from lem.records.task import Task

# Each column with no card: its key, who acts (its look), its title, its line when empty.
DONE = "done"
LANES = (
    Lane(key="you", actor="you", title="Waits for you", empty="Nothing waits for you"),
    Lane(key="build", actor="lead", title="Building", empty="No task builds"),
    Lane(
        key="checks",
        actor="gate",
        title="Checks and review",
        empty="No branch is checked or reviewed",
    ),
    Lane(key=DONE, actor=DONE, title="Done", empty="Nothing landed yet"),
)
CHECKS = frozenset(("ready", "landing", "open"))
ENDED = frozenset(("landed", "answered", "dropped"))
ASSETS = "/assets"


def lane_of(task: Task) -> str:
    """The key of the column that shows `task`."""
    if task.status in ENDED:
        return DONE
    if isinstance(task.hold, OwnerHold | BreakerHold):
        return "you"
    return "checks" if task.status in CHECKS else "build"


def line_of(task: Task) -> str:
    """The card's line: the status, and the kind of what holds the task."""
    if task.hold is None:
        return task.status
    kind = msgspec.to_builtins(task.hold)["kind"]
    return f"{task.status} · {kind}"


def card(task: Task) -> Card:
    """The card of `task`."""
    lines = task.ask.strip().splitlines()
    return Card(
        slug=task.slug,
        ask=lines[0] if lines else task.slug,
        status=task.status,
        line=line_of(task),
        since=clock.minute(task.since),
    )


def lane(key: str, records: tuple[Record, ...]) -> tuple[Card, ...]:
    """The cards of the column `key`, the longest in its state first; Done the newest
    first."""
    tasks = [record.task for record in records if lane_of(record.task) == key]
    tasks.sort(key=lambda task: task.since, reverse=key == DONE)
    return tuple(card(task) for task in tasks)


def kanban(
    records: tuple[Record, ...], *, host: str, workspace: str, version: str
) -> Kanban:
    """The kanban of the records of one workspace, at the version of its state folder."""
    lanes = tuple(
        msgspec.structs.replace(spec, cards=lane(spec.key, records)) for spec in LANES
    )
    return Kanban(
        title=f"Tasks · Lem · {workspace}",
        host=host,
        workspace=workspace,
        assets=ASSETS,
        stream=f"/{host}/{workspace}/stream",
        version=version,
        lanes=lanes,
    )
