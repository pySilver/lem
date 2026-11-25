"""`lem land checks`: each command of `checks.commands`, in order, at the root of the task's
worktree, its output in a file of the task's folder, and the run on record.

Each command starts in a process group of its own, and what it leaves running is stopped with
it. Each output is published at a path named by its round, its place and its digest, so a run
cut off and run again never changes a file the record cites. The load gate, `checks.serial`,
the removal of what the commands wrote and the criteria's check are the step `land-checks`'s.
"""

import os
import tempfile
from functools import partial
from typing import TYPE_CHECKING

from lem.app.landing import changes, frame, step
from lem.kernel import files, procs
from lem.model.landing import checks
from lem.records.journal.landing import CheckEnd, CommandEnd
from lem.records.landing.checks import Checked, Outcome

if TYPE_CHECKING:
    from pathlib import Path

    from lem.kernel.envelope import Envelope
    from lem.records.record import Record

SHELL = "/bin/sh"
# How long a command's group has to end after its term, then after its kill, in seconds.
GRACE = 10.0
SHORT = 12


def output_of(context: frame.Context, command: str) -> tuple[int, bytes]:
    """Run one command in the worktree: its exit code and its output."""
    with tempfile.TemporaryFile() as output:
        argv = [SHELL, "-c", command]
        proc = procs.start_group(argv, context.worktree, os.environ, output)
        code = proc.wait()
        procs.stop_group(proc, GRACE, GRACE, whole_group=True)
        output.seek(0)
        return code, output.read()


def published(context: frame.Context, place: int, body: bytes) -> str:
    """Publish a command's output in the task's folder, and give its path there."""
    landing = context.record.landing
    round_of = landing.round if landing else 1
    short = files.digest(body)[:SHORT]
    named = f"checks/r{round_of}-{place}-{short}.log"
    files.publish(context.folder / named, body)
    return named


def ran(context: frame.Context, place: int, command: str) -> Outcome:
    """Run one command, publish its output, and give its outcome."""
    code, body = output_of(context, command)
    lines = body.decode(errors="replace").strip().splitlines() or [""]
    named = published(context, place, body)
    return Outcome(
        command=command,
        exit=code,
        last=lines[-1].strip(),
        output=named,
        passed=not code,
    )


def checked(record: Record, *, run: Checked) -> Record:
    """The record with the run, and its end in the journal."""
    ends = tuple(
        CommandEnd(name=outcome.command, passed=outcome.passed, last=outcome.last)
        for outcome in run.outcomes
    )
    said = f"the checks {run.outcome}"
    entry = CheckEnd(at=run.at, outcome=run.outcome, say=said, commands=ends)
    return changes.noted(changes.landing(record, checked=run), entry)


def every(context: frame.Context) -> tuple[Outcome, ...]:
    """Each command's outcome, in the order of the settings."""
    commands = enumerate(context.world.rules.commands, 1)
    return tuple(ran(context, place, command) for place, command in commands)


def act(context: frame.Context) -> Checked:
    """Run the checks on the tip, and record the run."""
    world = context.world
    refused = checks.decide(context.record, world)
    if refused is not None:
        raise refused
    outcomes = every(context)
    refused = checks.left(clean=context.ports.git.clean(context.worktree))
    if refused is not None:
        raise refused
    passed = all(outcome.passed for outcome in outcomes)
    run = Checked(
        tip=world.tip or "",
        tree=world.tree or "",
        base=world.base,
        inputs=checks.inputs(world.rules),
        outcome="passed" if passed else "red",
        outcomes=outcomes,
        at=world.now,
    )
    context.write(context.record, partial(checked, run=run))
    return run


def run(folder: Path, slug: str) -> Envelope:
    """`lem land checks SLUG`."""
    return step.landed(folder, slug, "checks", act)
