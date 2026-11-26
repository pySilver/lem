"""`lem land checks SLUG --status` and `--stop` (`land.checks_status`, `checks_stop` and
`running_checks` on `main`).

Neither takes the step lock: each reads the lock's file and the process it names, so a look
never makes a real start fail. A run waits at the gate until its span of the checks begins;
its time counts from that start, against the last passed run of any task of the workspace. A
stop sends the run a term only while the lock is held by `checks`, and waits until that run
let it go: its commands end, and its end is on record, before the lock goes.
"""

import os
import signal
import time
from typing import TYPE_CHECKING

from lem.app.landing import checks_last, checks_since, checks_waits
from lem.kernel import clock
from lem.kernel.errors import Refusal
from lem.model.landing import checks_said
from lem.records.base import Frozen, Moment
from lem.store import places, steps, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record

# How long `--stop` waits for the run it stopped to end: the stop of a serial command takes up
# to its wrapper's grace, and the criteria's check its own grace for each command it runs. A
# guess with room, not a measurement (`STOP_WAIT` on `main`).
STOP_WAIT = 60.0
LOOK = 0.1


class Status(Frozen, frozen=True, kw_only=True):
    """Whether the task's checks run, since when and for how long, why they wait at the gate,
    the step that holds the lock when it is not the checks, the last passed run of the
    workspace and the tasks whose record did not read for it, whether this one is overdue and
    its line, and how the task's last run ended."""

    task: str
    running: bool
    pid: int | None = None
    since: Moment | None = None
    seconds: int | None = None
    waits: checks_waits.Waited | None = None
    step: str | None = None
    last_seconds: int | None = None
    unread: tuple[str, ...] = ()
    overdue: bool = False
    say: str | None = None
    ended: checks_last.Ended | None = None


class Stopped(Frozen, frozen=True, kw_only=True):
    """What `--stop` did: whether it stopped a run, its process, and how the last run ended."""

    task: str
    stopped: bool
    pid: int | None = None
    ended: checks_last.Ended | None = None


def status(folder: Path, slug: str) -> Status:
    """The checks of the task `slug`, as they stand now."""
    state = places.workspace(folder).state
    record = tasks.read(state, slug)
    holder = steps.holder_of(places.task_folder(state, slug) / steps.LOCK)
    ended = checks_last.ended_of(record)
    if holder is None:
        return Status(task=slug, running=False, ended=ended)
    if holder.step != "checks":
        return Status(task=slug, running=False, step=holder.step, ended=ended)
    return watched(record, state, holder, ended)


def watched(
    record: Record, state: Path, holder: steps.Holder, ended: checks_last.Ended | None
) -> Status:
    """The status of a run that holds the lock."""
    slug = record.task.slug
    run = checks_since.running(record, state, holder, clock.now())
    said = checks_said.overdue(run.seconds, run.last)
    return Status(
        task=slug,
        running=True,
        pid=holder.pid,
        since=run.since,
        seconds=run.seconds,
        waits=run.waits,
        last_seconds=run.last,
        unread=run.unread,
        overdue=said is not None,
        say=said and f"{slug}: {said}",
        ended=ended,
    )


def stop(folder: Path, slug: str) -> Stopped:
    """Stop the task's checks, and wait until the run let the lock go."""
    state = places.workspace(folder).state
    path = places.task_folder(state, slug) / steps.LOCK
    holder = steps.holder_of(path)
    pid = None
    if holder is not None and holder.step == "checks":
        pid = holder.pid
    if pid is not None and termed(slug, pid):
        waited(slug, path, pid)
    else:
        pid = None
    ended = checks_last.ended_of(tasks.read(state, slug))
    return Stopped(task=slug, stopped=pid is not None, pid=pid, ended=ended)


def termed(slug: str, pid: int) -> bool:
    """Send the run a term; False when its process is gone."""
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return False
    except PermissionError as error:
        raise Refusal(
            "stop",
            f"the checks of {slug} run in process {pid}, which this user may not stop "
            f"({error.strerror})",
            "the user that started them stops them",
        ) from error
    return True


def waited(slug: str, path: Path, pid: int) -> None:
    """Wait until the run of `pid` let the lock go: it takes its holder's line away last,
    after its commands ended and its result is kept."""
    deadline = time.monotonic() + STOP_WAIT
    while time.monotonic() < deadline:
        holder = steps.holder_of(path)
        if holder is None or holder.pid != pid:
            return
        time.sleep(LOOK)
    raise Refusal(
        "stop",
        f"the checks of {slug} were asked to stop, and process {pid} still runs after "
        f"{STOP_WAIT:g} s",
        f"`lem land checks {slug} --stop` asks again, and `lem land checks {slug} --status` "
        "says whether they still run",
    )
