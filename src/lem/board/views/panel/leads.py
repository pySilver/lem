"""Who works on a task, in words a developer needs no glossary for (`board_model.LEAD` and
`lead_of` on `main`): its tag, the large card's head while it builds, and the stat's line."""

from types import MappingProxyType
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from lem.records.record import Record


class Lead(NamedTuple):
    """Who works on a task: the stat's value, the large card's head, the stat's line."""

    tag: str
    head: str
    stat: str


ONE_AGENT = "one agent"
LEADS = MappingProxyType(
    {
        "session": Lead(
            "plan talk",
            "Its companion talks the plan through",
            "a companion talks the plan through, with the reviewer in its other pane",
        ),
        "talked": Lead(
            ONE_AGENT,
            "An agent builds it",
            "one agent builds the plan its companion talked through",
        ),
        "builder": Lead(
            ONE_AGENT,
            "An agent plans and builds it",
            "one agent plans it, and a fresh builder builds each task of the plan",
        ),
        "small": Lead(
            "one builder",
            "One builder makes the change",
            "one builder makes the change, with no lead and no plan",
        ),
    }
)


def lead_of(record: Record) -> Lead | None:
    """Who works on the task, or None before a lead started."""
    task = record.task
    if task.lead is None:
        return None
    if task.lead != "builder":
        return LEADS[task.lead]
    talked = task.talk is not None or any(
        span.name == "plan-talk" for span in task.spans
    )
    return LEADS["talked" if talked else "builder"]
