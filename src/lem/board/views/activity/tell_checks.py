"""The feed's words of a run of the checks that ended: each command with its last line, then
the run's end with Lem's line, how long it took and on which commit (`gate` and `gate.end` of
`main`'s `describe` and `SAYS`). A command has no moment of its own: it is told at the run's
end."""

import re
from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.board.inputs.clock import length
from lem.board.views.activity.told import ALERT, BAD, CHECK, DONE, LEM, Told

if TYPE_CHECKING:
    from lem.board.inputs.text import Look
    from lem.records.journal.landing import CheckEnd, CommandEnd

HEADS = MappingProxyType(
    {
        "passed": "The checks passed",
        "red": "The checks are red",
        "refused": "The checks refused the change",
        "stopped": "The checks were stopped",
    }
)
# A commit as the feed names it.
SHORT = 9
# Lem's line of a run names its task first (`SLUG: the checks passed`): the task's feed does not.
NAMED = re.compile(r"^[a-z0-9-]+: ")


def ended(entry: CheckEnd) -> tuple[Told, ...]:
    """Each command of the run, then its end."""
    return (*map(command, entry.commands), end(entry))


def command(ran: CommandEnd) -> Told:
    """One command, in monospace, with its last line under it."""
    if ran.passed:
        return Told(DONE, CHECK, "Check passed", ran.name, ran.last, mono=True)
    return Told(BAD, ALERT, "Check failed", ran.name, ran.last, mono=True)


def end(entry: CheckEnd) -> Told:
    """The run's end: its result, Lem's line, and how long it ran on which commit."""
    said = NAMED.sub("", entry.say)
    ran = took(entry)
    look, icon = look_of(entry)
    if said:
        return Told(look, icon, HEADS[entry.outcome], said, ran)
    return Told(look, icon, HEADS[entry.outcome], ran)


def took(entry: CheckEnd) -> str:
    """`after 4m 26s on 3f2a1b9c0`, as far as the run's entry holds them, with the polish
    pass's run of the criteria's tests that the run took when it took one."""
    seconds = None if entry.seconds is None else length(entry.seconds)
    parts = (
        f"after {seconds}" if seconds else "",
        f"on {short(entry.tip)}" if entry.tip else "",
    )
    ran = " ".join(part for part in parts if part)
    if entry.taken is None:
        return ran
    taken = short(entry.taken)
    said = f"the tests of the criteria taken from the polish pass at {taken}, not run again"
    return f"{ran} · {said}" if ran else said


def short(commit: str) -> str:
    """A commit as the feed names it."""
    return commit[:SHORT]


def look_of(entry: CheckEnd) -> tuple[Look, str]:
    """A passed run is done, a stopped one Lem's, any other a fault."""
    if entry.outcome == "passed":
        return DONE, CHECK
    if entry.outcome == "stopped":
        return LEM, "xmark"
    return BAD, ALERT
