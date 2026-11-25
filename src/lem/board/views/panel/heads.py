"""The head of a task's large card, what it does now in words (`board_model.now_head` on
`main`): a stop two releases back, a park or a block first, then the owner's hold or a
breaker (`held_head.py`), then the task's status, its landing's step (`landing_head.py`) and
its merge."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.board.views import merge_state, rule, telling
from lem.board.views.panel import held_head, landing_head
from lem.board.views.panel.leads import lead_of
from lem.model.owner import merging
from lem.records.holds import Blocked, Parked, ReleaseHold

if TYPE_CHECKING:
    from lem.board.views.world import Seen
    from lem.records.record import Record

OLDER_RELEASE = "It began on an older release of Lem"
# The head of each status that says it alone.
PLAIN = MappingProxyType(
    {
        "shaping": "Its session opened: it reads the request",
        "ready": "Waits for its checks",
        "landed": "Landed",
        "dropped": "Dropped",
        "answered": "Answered: it ended with a report and nothing to merge",
    }
)
# The head of an open pull request by who its merge waits for.
PROPOSED = MappingProxyType(
    {
        "reads": "Proposed: the merge agent reads it",
        "merges": "Proposed: the merge agent found nothing for you, and Lem merges it",
        "relands": "Proposed: Lem lands it again on the moved base",
    }
)


def now_head(seen: Seen, after: str | None = None, *, alone: bool = False) -> str:
    """What the task of `seen` does now; `after` names the dropped task it was queued
    behind, and `alone` says it runs without the owner."""
    task = seen.record.task
    hold = task.hold
    if task.status in rule.ENDED or hold is None:
        return status_head(seen.record, after)
    if isinstance(hold, ReleaseHold):
        return OLDER_RELEASE
    if isinstance(hold, Parked):
        return "Parked: nobody works on it until you bring it back"
    if isinstance(hold, Blocked):
        return blocked(hold)
    return held_head.held(seen, alone=alone)


def blocked(hold: Blocked) -> str:
    """A block: the base a task of its own repairs, or a session that stopped."""
    if hold.after is not None:
        return "It waits for the base: a task of its own repairs the check that fails there"
    return "Its session stopped: it waits for your word"


def status_head(record: Record, after: str | None) -> str:
    """The head of a task no hold holds, by its status."""
    task = record.task
    if task.status == "queued":
        return queued(record, after)
    if task.status == "building":
        return building(record)
    if task.status == "planned":
        return planned(record)
    if task.status in {"landing", "open"}:
        return telling.waiting(record) or merge_state.said(record) or moving(record)
    return PLAIN.get(task.status, f"Status “{task.status}”")


def planned(record: Record) -> str:
    """A plan no hold of the owner holds: its plan talk, or the agent after it."""
    if record.task.talk is not None:
        return "The plan talk is done: the plan waits for the agent that builds it"
    return "The plan waits for its plan talk"


def queued(record: Record, after: str | None) -> str:
    """A queued task: the dropped task it waited for, another task, or its start."""
    if after is not None:
        return f"{after} was dropped: your word starts or ends this task"
    return "Waits for another task" if record.task.after else "Waits to start"


def building(record: Record) -> str:
    """A task that builds: its investigator, or who works on it."""
    if rule.investigates(record.task):
        return "Its investigator examines it, before any criterion"
    lead = lead_of(record)
    return lead.head if lead else "An agent plans and builds it"


def moving(record: Record) -> str:
    """A landing's step, or the merge an open pull request waits for."""
    if record.task.status == "landing":
        return landing_head.landing(record)
    wait = merging.merge_wait(record) or ""
    return PROPOSED.get(wait, "Proposed: it waits for your merge")
