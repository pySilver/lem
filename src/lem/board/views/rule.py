"""The words of each state of a task on the board (`board_model.STATUS` on `main`, in the words of
SKILL.md's table): who acts, its look, its label, its icon, and whether it moves."""

from types import MappingProxyType
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from lem.board.inputs.text import Look
    from lem.records.task import Task


class Said(NamedTuple):
    """A state's look, who acts in it, its words, its icon, and whether it moves."""

    look: Look
    who: str
    label: str
    icon: str
    live: bool = False


ENDED = frozenset(("landed", "answered", "dropped"))
LEM = "Lem"
AGENT = "The agent"
NOBODY = "Nobody"
PAGE = "file-lines"
QUIET: Look = "quiet"
OWN: Look = "lem"
STATUS = MappingProxyType(
    {
        "queued": Said(QUIET, LEM, "Queued", "clock"),
        "shaping": Said(OWN, LEM, "Shaping", "magnifying-glass", live=True),
        "building": Said("lead", AGENT, "Building", "code", live=True),
        "planned": Said(OWN, LEM, "Planned", PAGE),
        "ready": Said("gate", LEM, "Ready for its checks", "flag"),
        "landing": Said("gate", "The checks", "Checks and review", "play", live=True),
        "open": Said("you", "You", "Waits for the merge", "code-branch"),
        "landed": Said("done", NOBODY, "Landed", "check"),
        "dropped": Said(QUIET, NOBODY, "Dropped", "xmark"),
        "answered": Said("done", NOBODY, "Answered", PAGE),
    }
)
HELD = Said("you", "You", "Waits for you", "user", live=True)
PARKED = Said(QUIET, NOBODY, "Parked", "folder")
BLOCKED = Said("bad", LEM, "Blocked", "triangle-exclamation")
INVESTIGATES = Said("lead", "The investigator", "Investigating", "eye", live=True)
WORKS = Said(OWN, "The task's session", "Works on your answer", "play", live=True)
READING = Said(QUIET, LEM, "The personas read the criteria", "users", live=True)
WRITES = Said(OWN, LEM, "Lem writes the criteria", PAGE, live=True)


def investigates(task: Task) -> bool:
    """Whether the task's investigation runs: it builds, and its investigation has no call
    yet."""
    found = task.investigation
    return task.status == "building" and found is not None and found.call is None
