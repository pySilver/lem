"""What a view holds, in the one line of the bar above it (`board_pages.summary_of` and each
page's summary on `main`): first how many tasks wait for the owner, as the sidebar counts them,
then what builds, what Lem does, what is checked, queued, blocked and parked."""

from types import MappingProxyType
from typing import NamedTuple

from lem.board.inputs.names import plural
from lem.board.views import rule
from lem.board.views.frame import counted
from lem.board.views.kanban_order import SHOWN

# The title of each view, and its line when it is fixed.
TITLES = MappingProxyType(
    {
        "tasks": "Tasks",
        "waits": "Waits for you",
        "backlog": "Backlog",
        "activity": "Activity",
        "done": "Older ended tasks",
        "new": "New task",
    }
)
FIXED = MappingProxyType(
    {
        "backlog": (
            "The reviewer's items, then the items of the backlog by the worth each one "
            "gives itself"
        ),
        "activity": "What each task waited on today, and every event, the newest first",
        "new": "A new task, in your words",
    }
)
BUILD = "build"


class Part(NamedTuple):
    """A part of the line of Tasks: its column, the label of a state or None, the status or
    None, and its words for one task and for more."""

    column: str
    label: str | None
    status: str | None
    one: str
    more: str


PARTS = (
    Part(BUILD, None, "building", "builds", BUILD),
    Part(
        BUILD,
        rule.WRITES.label,
        None,
        "whose criteria Lem writes",
        "whose criteria Lem writes",
    ),
    Part(
        BUILD,
        rule.READING.label,
        None,
        "with the personas’ read of its criteria",
        "with the personas’ read of their criteria",
    ),
    Part(
        BUILD,
        rule.WORKS.label,
        None,
        "whose session works on your answer",
        "whose session works on your answer",
    ),
    Part("checks", None, None, "in checks and review", "in checks and review"),
    Part(BUILD, None, "queued", "queued", "queued"),
    Part(BUILD, None, "planned", "waits for its plan talk", "wait for their plan talk"),
    Part(BUILD, rule.BLOCKED.label, None, "blocked", "blocked"),
    Part("parked", None, None, "parked", "parked"),
)


def tasks_line(counts: counted.Counted) -> str:
    """The line of Tasks."""
    parts = [counted.waits_said(counts.waits)] if counts.waits else []
    parts.extend(filter(None, (part_said(counts, part) for part in PARTS)))
    if parts:
        line = ", ".join(parts)
        return line[:1].upper() + line[1:]
    if counts.placed:
        return "Nothing runs"
    return "Waiting for the first task: type /lem and an ask in any session"


def part_said(counts: counted.Counted, part: Part) -> str:
    """One part of the line, or "" when no task is of it."""
    count = sum(
        1
        for seen, where in counts.placed
        if where.column == part.column
        and part.label in {None, where.label}
        and part.status in {None, seen.record.task.status}
    )
    words = part.one if count == 1 else part.more
    return f"{count} {words}" if count else ""


def waits_line(counts: counted.Counted) -> str:
    """The line of Waits for you."""
    if not counts.waits:
        return "Nothing waits for you"
    return f"{counted.tasks_said(counts.waits)}, the most pressing first"


def older_line(older: int) -> str:
    """The line of the page of the older ended tasks."""
    if older:
        return (
            f"The {plural(older, 'ended task')} Done has no card for, the newest first"
        )
    return "Every ended task has its card in Done"


def said(view: str, counts: counted.Counted) -> tuple[str, str]:
    """The title of the view and its line."""
    line = FIXED.get(view)
    if line:
        return TITLES[view], line
    if view == "waits":
        line = waits_line(counts)
    elif view == "done":
        line = older_line(max(0, counts.count("done") - SHOWN))
    else:
        line = tasks_line(counts)
    return TITLES[view], line
