"""A landing whose run of the checks was stopped, red or refused, and that has not gone on since
(`board_model.settle`'s `checks_stop` and `CHECKS_END` on `main`): it is Lem's, waiting for the
owner's word after a stop, starting a builder that repairs it after the others."""

import re
from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.board.views.rule import Said
from lem.records.journal.landing import CheckEnd
from lem.records.journal.task import StateNoted

if TYPE_CHECKING:
    from lem.records.record import Record

ALERT = "triangle-exclamation"
STOPPED = "stopped"
# How a run of the checks ended, as the card says it.
ENDS = MappingProxyType(
    {
        "red": Said("lem", "Lem", "Checks red", ALERT),
        "refused": Said("lem", "Lem", "Checks refused", ALERT),
        STOPPED: Said("lem", "Lem", "Checks stopped", "xmark"),
    }
)
HEADS = MappingProxyType(
    {
        "red": "the checks are red",
        "refused": "the checks refused the change",
        STOPPED: "the checks were stopped",
    }
)
SLUG = re.compile(r"^[a-z0-9-]+: ")


def ended(record: Record) -> CheckEnd | None:
    """The run of a landing that ended stopped, red or refused, with no state after it."""
    if record.task.status != "landing":
        return None
    for entry in reversed(record.journal):
        if isinstance(entry, StateNoted):
            return None
        if isinstance(entry, CheckEnd):
            return None if entry.outcome == "passed" else entry
    return None


def line(record: Record, end: CheckEnd) -> str:
    """What the card says of the run: its own line, or what follows from its end."""
    said = SLUG.sub("", end.say)
    head = HEADS[end.outcome]
    if not said and end.outcome == STOPPED:
        said = f"{head}; the landing waits for your word"
    elif not said:
        said = f"{head}; a builder repairs it, nothing for you"
    if end.outcome != STOPPED:
        return said
    slug = record.task.slug
    return (
        f"{said}. In the task's session, /lem land starts them again and /lem drop "
        f"{slug} drops the task"
    )
