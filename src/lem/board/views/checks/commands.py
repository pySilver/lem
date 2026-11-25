"""The card of the checks on the tab Checks and review (`board_task.checks_tab` and `log_link`,
`board_model.checks_end` and `say_of` on `main`): each command of the last run with its output on
Artifacts, its last line and the commit it ran on; or, while a landing's run ended stopped, red or
refused with no command, that end and its line.

No record holds when each command ended (`notes/board-inputs.md`, "A command's moment"): each
shows the run's end.
"""

import re
from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.board.inputs.clock import stamp
from lem.board.inputs.names import plural
from lem.board.inputs.parts import Row
from lem.board.inputs.task.checks import Command
from lem.board.views.artifacts.addresses import file_link
from lem.records.journal.landing import CheckEnd

if TYPE_CHECKING:
    from lem.board.inputs.parts import Link
    from lem.board.views.world import Seen, World
    from lem.records.landing.checks import Checked, Outcome

# The head of a run's end, by its outcome.
ENDS = MappingProxyType(
    {
        "passed": "The checks passed",
        "red": "The checks are red",
        "refused": "The checks refused the change",
        "stopped": "The checks were stopped",
    }
)
SLUG_FIRST = re.compile(r"^[a-z0-9-]+: ")
SHORT = 7


def command(world: World, seen: Seen, checked: Checked, at: int) -> Command:
    """The command `at` of the run, numbered from 0."""
    ran = checked.outcomes[at]
    green = ran.passed
    return Command(
        id=f"gate-{at}",
        look="done" if green else "bad",
        icon="check" if green else "triangle-exclamation",
        word="green" if green else f"exit {ran.exit}",
        command=ran.command,
        output=output(world, seen, ran),
        last=ran.last or None,
        tip=checked.tip[:SHORT],
        time=stamp(checked.at, world.clock.now, world.clock.zone),
    )


def output(world: World, seen: Seen, ran: Outcome) -> Link | None:
    """The link to a command's whole output on Artifacts, where the task's folder has it."""
    if ran.output not in seen.files:
        return None
    title = f"Open its output, {ran.output}"
    return file_link(world, seen.record.task.slug, ran.output, "output", title)


def said_of(checked: Checked | None) -> str | None:
    """The card's line: how many commands were green, or how many of them red."""
    if checked is None or not checked.outcomes:
        return None
    count = len(checked.outcomes)
    red = sum(1 for ran in checked.outcomes if not ran.passed)
    return f"{red} of {count} red" if red else f"{plural(count, 'command')} green"


def ended_run(seen: Seen) -> Row | None:
    """A landing's run that ended stopped, red or refused with no command, as one row."""
    record = seen.record
    ends = (entry for entry in reversed(record.journal) if isinstance(entry, CheckEnd))
    end = next(ends, None)
    if record.task.status != "landing" or end is None or end.outcome == "passed":
        return None
    stopped = end.outcome == "stopped"
    said = SLUG_FIRST.sub("", end.say)
    return Row(
        id="gate-end",
        look="lem" if stopped else "bad",
        icon="xmark" if stopped else "triangle-exclamation",
        head=ENDS[end.outcome],
        subs=(said,) if said else (),
    )


def listed(world: World, seen: Seen) -> tuple[Command, ...]:
    """Each command of the task's last run of the checks."""
    landing = seen.record.landing
    checked = landing.checked if landing else None
    if checked is None:
        return ()
    count = len(checked.outcomes)
    return tuple(command(world, seen, checked, at) for at in range(count))
