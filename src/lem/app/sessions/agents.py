"""Whether an agent runs in a session's main pane, and the line a scheduled job started it with,
from the words of the pane's program (`Terminal.foregrounds`), as agterm's tree gave them on
2026-11-21 and 2026-11-23 (`session.agent_runs` and `session.job_line` on `main`).

The program is an agent the owner started by hand (a word whose file is an agent's,
`/.../bin/claude ...` or `node /.../claude`), or the shell of a launch line, whose `-c` string
runs the agent. A shell with no command, or the empty foreground of an idle shell, is no agent: a
dead agent leaves one. The cronn skill's job script ends in `exec ... "$JOB_AGENT" $JOB_ARGS
"$JOB_PROMPT"`, so a job's prompt is the last word of its agent's command.
"""

import re
import shlex
from pathlib import PurePath
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from lem.ports.terminal import Foreground

# The programs that count as the task's agent in the pane, by the name of their file.
AGENTS = frozenset(("claude", "codex"))
# A shell's option that runs the next word as a command: `-c`, a cluster with it (`-lc`), or
# fish's `--command`.
SHELL_COMMAND = re.compile(r"-[a-zA-Z]*c[a-zA-Z]*|--command")
# A word of a command that sets a variable for it, `NAME=value`.
ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=.*", re.DOTALL)
# The line a scheduled job starts its agent with: `/lem night`, `/lem night N`, `/lem retro`.
JOB_LINE = re.compile(r"/lem (?:night(?: [1-9][0-9]*)?|retro)")
# A session opened this long ago counts as live while its agent starts: the login shell runs
# first, and a second open in that time must not open another. A guess (`session.STARTING`).
STARTING = 60


def command_agent(text: str) -> bool:
    """Whether a shell's `-c` string runs an agent: its first word after the `NAME=value` words
    is an agent's file; a string that does not read as a shell's words counts when one plain
    word of it is."""
    try:
        words = shlex.split(text)
    except ValueError:
        return any(PurePath(word).name in AGENTS for word in text.split())
    first = next((word for word in words if not ASSIGNMENT.fullmatch(word)), None)
    return first is not None and PurePath(first).name in AGENTS


def agent_runs(ground: Foreground) -> bool | None:
    """Whether the program in the main pane is an agent; None while the pane is not drawn."""
    if ground is None:
        return None
    pairs = zip(("", *ground), ground, strict=False)
    return any(
        command_agent(word)
        if SHELL_COMMAND.fullmatch(before)
        else PurePath(word).name in AGENTS
        for before, word in pairs
    )


def job_line(ground: Foreground) -> str | None:
    """The job's line of a session a scheduled job started for one run, else None: an agent's
    command whose last word is the line."""
    if not ground or not ground[1:]:
        return None
    line = " ".join(ground[-1].split())
    if not JOB_LINE.fullmatch(line):
        return None
    names = {PurePath(word).name for word in ground[:-1]}
    return line if names & AGENTS else None


def live(ground: Foreground, *, listed: bool, opened: datetime, now: datetime) -> bool:
    """Whether a session still carries its task: the terminal lists it, and an agent runs in
    it, or the terminal does not know yet, or it opened under STARTING seconds ago."""
    if not listed:
        return False
    if agent_runs(ground) is not False:
        return True
    return (now - opened).total_seconds() < STARTING
