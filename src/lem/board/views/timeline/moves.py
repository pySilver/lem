"""Who holds the work in a state of the task where no span says it, and its words (the heads of
`time_of`'s state blocks on `main`): the owner while his answer, a breaker or a block of his
holds it, Lem while the task is queued, reads its request, waits for its checks or its plan
talk, or the base is red; the owner or the merge agent while its pull request waits for the
merge. A parked or ended task holds nobody. A build and a landing are `blocks.py`'s.
"""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.board.views import words
from lem.board.views.activity.tell_task import talked
from lem.board.views.timeline import shapes

if TYPE_CHECKING:
    from lem.records.journal.task import StateNoted
    from lem.records.record import Record

BLOCKED = frozenset(("blocked", "release"))
FIXED = MappingProxyType(
    {
        "shaping": (shapes.LEM, "Lem reads the request"),
        "ready": (shapes.LEM, "Ready: it waits for its checks"),
    }
)
# The stage's line of a red base (`BASE_RED` on `main`).
BASE_RED = "the base is red"


def held_by(record: Record, noted: StateNoted) -> tuple[str, str] | None:
    """The lane and head of a state where no span says who holds the work."""
    hold = noted.hold
    line = noted.line or ""
    if hold == "owner":
        return shapes.YOU, owner_head(noted.status, line)
    if hold == "breaker":
        return shapes.YOU, "The build stopped: its breaker waits for you"
    if hold in BLOCKED:
        return blocked(line)
    if hold is not None:
        return None
    return by_status(record, noted.status)


def line_of(record: Record, noted: StateNoted) -> str:
    """The state's line in the board's words."""
    line = noted.line or ""
    if not line:
        return ""
    return words.said(line, talked=talked(record.task, noted.at))


def owner_head(status: str, line: str) -> str:
    """What waits for the owner's answer: the criteria, the plan, or another step."""
    if "criteria wait" in line:
        return "The criteria wait for your yes"
    if status == "planned":
        return "The plan waits for you"
    return "It waits for you"


def blocked(line: str) -> tuple[str, str]:
    """A block: Lem's while the base is red, else the owner's."""
    if line.strip() == BASE_RED:
        return shapes.LEM, "Blocked: it waits for the base to be green again"
    return shapes.YOU, "Blocked: it waits for your word"


def by_status(record: Record, status: str) -> tuple[str, str] | None:
    """A state with no hold, by its status."""
    task = record.task
    if status == "queued":
        waits = "for another task" if task.after else "to start"
        return shapes.LEM, f"Queued: it waits {waits}"
    if status == "planned":
        return planned(record)
    if status == "open":
        return waits_for_merge(record)
    return FIXED.get(status)


def planned(record: Record) -> tuple[str, str]:
    """A plan that waits: for its plan talk, or for the agent that builds it after one."""
    if record.task.talk is not None:
        return (
            shapes.LEM,
            "The plan talk is done: the plan waits for the agent that builds it",
        )
    return shapes.LEM, "The plan waits for its plan talk"


def waits_for_merge(record: Record) -> tuple[str, str]:
    """An open pull request: the owner's merge, or the merge agent's read."""
    landing = record.landing
    proposed = landing.proposed if landing else None
    if proposed is not None and proposed.who_acts == "merger":
        return shapes.MERGER, "The merge agent reads it"
    return shapes.YOU, "It waits for your merge"
