"""`lem land checks`: each command of `checks.commands`, in order, at the root of the task's
worktree, then, when they all passed, each command of `checks.serial` under the repository's one
serial lock (`lem serial`), each with its output in a file of the task's folder (`land.
checks_body` on `main`).

Each command starts in a process group of its own, and what it leaves running is stopped with
it, also when the run is stopped in the middle (`checks_output.py`). Each output is published
at a path named by its round, its place and its digest, so a run cut off and run again never
changes a file the record cites. The step itself, from the gate to the record, is `checks_step.py`.
"""

import sys
from typing import TYPE_CHECKING

from lem.app.landing import checks_output
from lem.kernel import files
from lem.records.landing.checks import Outcome

if TYPE_CHECKING:
    from lem.app.landing import frame

SHELL = "/bin/sh"
# How long a command's group has to end after its term, in seconds; a serial command's
# wrapper (`lem serial`) gets the time of its own cleanup after the term: a term to its
# command, 3 s, a kill, 3 s more, and one second for its exit (`SERIAL_GRACE` on `main`).
GRACE = checks_output.GRACE
SERIAL_GRACE = 7.0
SHORT = 12


def output_of(context: frame.Context, command: str) -> tuple[int, bytes]:
    """Run one command of `checks.commands` in the worktree: its exit code and its output."""
    return checks_output.ended([SHELL, "-c", command], context.worktree, GRACE)


def published(context: frame.Context, place: int, body: bytes) -> str:
    """Publish a command's output in the task's folder, and give its path there."""
    landing = context.record.landing
    round_of = landing.round if landing else 1
    short = files.digest(body)[:SHORT]
    named = f"checks/r{round_of}-{place}-{short}.log"
    files.publish(context.folder / named, body)
    return named


def outcome_of(
    context: frame.Context, place: int, command: str, ran: tuple[int, bytes]
) -> Outcome:
    """One command's outcome, its output published."""
    code, body = ran
    lines = body.decode(errors="replace").strip().splitlines() or [""]
    return Outcome(
        command=command,
        exit=code,
        last=lines[-1].strip(),
        output=published(context, place, body),
        passed=not code,
        serial=place > len(context.world.rules.commands),
    )


def every(context: frame.Context) -> tuple[Outcome, ...]:
    """Each command of `checks.commands`, in the order of the settings."""
    commands = enumerate(context.world.rules.commands, 1)
    return tuple(
        outcome_of(context, place, command, output_of(context, command))
        for place, command in commands
    )


def serial_of(context: frame.Context, command: str) -> tuple[int, bytes]:
    """Run one command of `checks.serial` in the worktree through `lem serial`."""
    checkout = str(context.workspace.checkout)
    argv = [
        sys.executable,
        "-B",
        "-m",
        "lem",
        "--repo",
        checkout,
        "serial",
        "--",
        command,
    ]
    return checks_output.ended(argv, context.worktree, SERIAL_GRACE)


def serials(context: frame.Context) -> tuple[Outcome, ...]:
    """Each command of `checks.serial`, after the others, under the serial lock."""
    rules = context.world.rules
    numbered = enumerate(rules.serial, len(rules.commands) + 1)
    return tuple(
        outcome_of(context, place, command, serial_of(context, command))
        for place, command in numbered
    )
