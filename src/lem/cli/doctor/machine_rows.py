"""The rows of this machine's settings: the load gate of the landing's checks, and the tokens
past which a task's session compacts.

The values are the settings in force (`settings.load.settings_of`); a file that does not read is
the row's detail, with what stops until it reads.
"""

import os
from typing import TYPE_CHECKING

from lem.cli.doctor.row import OPTIONAL, Row
from lem.kernel import paths
from lem.settings import places
from lem.settings.load import settings_of

if TYPE_CHECKING:
    from lem.cli.doctor.look import Look
    from lem.settings.load import Loaded

LOAD_LINE = "lem settings set load.start N --machine"
HANDOFF_LINE = "lem settings set handoff.tokens N --machine"
LOAD_USED_FOR = (
    "the checks of a landing start only while the machine's load average is below the "
    "number set for this machine"
)
HANDOFF_USED_FOR = (
    "each task's session compacts itself past this number of tokens, with the handoff's "
    "form as its summary"
)


def settled(look: Look) -> Loaded:
    """The machine's settings in force; refused when a file does not read."""
    return settings_of(None, look.environ)


def machine_file(look: Look) -> str:
    """The machine's own settings file, as a person writes it."""
    path = paths.home(look.environ) / places.MACHINE
    return places.shown(path, look.environ)


def load_now() -> str:
    """The load average now, and the cores."""
    load = round(os.getloadavg()[0], 1)
    cores = os.cpu_count()
    return f"{load:g} now, on {cores} cores"


def gate_said(look: Look, loaded: Loaded) -> tuple[str, str | None]:
    """What the gate is now, and what happens without one."""
    start = loaded.settings.load.start
    now = load_now()
    where = machine_file(look)
    if not start:
        return (
            f"no gate on this machine (load.start = 0); the load average is {now}",
            (
                f"the checks of every landing start at once, whatever the load. "
                f"`{LOAD_LINE}` sets a number in {where}, for every repository on this "
                "machine"
            ),
        )
    whose = ", Lem's default" if loaded.sources["load.start"] == places.DEFAULT else ""
    said = f"the checks start below a load average of {start:g}{whose}; it is {now} ({where})"
    return said, None


def load_row(look: Look) -> Row:
    """The load average under which the checks of a landing start on this machine."""
    loaded = settled(look)
    detail, without = gate_said(look, loaded)
    return Row(
        name="load gate",
        need=OPTIONAL,
        found=bool(loaded.settings.load.start),
        detail=detail,
        used_for=LOAD_USED_FOR,
        without_it=without,
        line=LOAD_LINE,
    )


def handoff_row(look: Look) -> Row:
    """Past how many tokens a task's session compacts itself, on this machine."""
    loaded = settled(look)
    tokens = loaded.settings.handoff.tokens
    written = loaded.sources["handoff.tokens"] != places.DEFAULT
    source = f"set in {machine_file(look)}" if written else "default"
    detail = f"handoff tokens: {tokens} ({source})"
    if not tokens:
        detail = (
            "handoff tokens: 0, so Lem sets nothing and Claude Code compacts at its own "
            "trigger"
        )
    return Row(
        name="handoff tokens",
        need=OPTIONAL,
        found=True,
        detail=detail,
        used_for=HANDOFF_USED_FOR,
        without_it=None,
        line=HANDOFF_LINE,
    )
