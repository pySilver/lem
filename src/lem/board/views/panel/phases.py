"""The phases of a task's progress card (`board_model.phases_of`, `phase_index` and
`progress_of` on `main`): their names, the one it reached, how many are past, and the line under
each. A task that waits for the owner or is held stays where it got to."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.board.inputs.task.now import Phase
from lem.board.views import rule
from lem.board.views.panel import plan
from lem.board.views.panel.phase_lines import line_of

if TYPE_CHECKING:
    from lem.records.record import Record

PHASES = ("Criteria", "Plan", "Build", "Checks", "Review", "Proposed", "Landed")
SMALL_PHASES = ("Change", "Checks", "Review", "Proposed", "Landed")
ANSWERED = "Answered"
INVESTIGATION = "Investigation"
# The phase each status reached, past the build.
REACHED = MappingProxyType({"landed": 7, "open": 5, "ready": 3, "planned": 1})


def phases(record: Record) -> tuple[Phase, ...]:
    """The task's phases, each with its line, the past ones and the one now."""
    lead = 0 if record.task.investigation is None else 1
    names = names_of(record, lead=lead)
    places = placed(record, lead, len(names))
    return tuple(
        Phase(
            name=name,
            sub=line_of(record, step, lead) or None,
            past=step < places[1],
            current=step == places[0],
        )
        for step, name in enumerate(names)
    )


def placed(record: Record, lead: int, count: int) -> tuple[int, int]:
    """The phase now (-1 for none) and how many are past, of `count` phases after `lead` of
    an investigation."""
    task = record.task
    if rule.investigates(task):
        return 0, 0
    if task.status == "answered":
        return -1, count
    at = index(record) + lead
    return at, at


def names_of(record: Record, *, lead: int) -> tuple[str, ...]:
    """The names of the task's phases: its investigation first when it had one."""
    task = record.task
    first = (INVESTIGATION,) if lead else ()
    if task.status == "answered":
        return (*first, ANSWERED)
    return (*first, *(SMALL_PHASES if task.lead == "small" else PHASES))


def index(record: Record) -> int:
    """The phase the task reached, among its track's phases."""
    task = record.task
    if task.lead != "small":
        return full_index(record)
    if plan.reached(record) == "landed":
        return len(SMALL_PHASES)
    return max(0, full_index(record) - 2)


def full_index(record: Record) -> int:
    """The phase the task reached, among the standard track's."""
    reached = plan.reached(record)
    found = REACHED.get(reached)
    if found is not None:
        return found
    if reached == "landing":
        return 4 if record.landing and record.landing.reviews else 3
    if reached == "building":
        started = record.task.plan is not None or plan.progress(record) is not None
        return 2 if started else 1
    return 0
