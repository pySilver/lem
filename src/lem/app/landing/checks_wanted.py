"""Which runs of the line another open task waits for (`land.waited_for` and `line_wanted` on
`main`): a task queued after it, or a task blocked because the base is red, whose `after` names
the repair it waits for. Read from each repository's records at each look, so that a task
queued after the entries were made counts at the next look; and the look itself (`gate_look`
on `main`), whose start writes itself into `load.lock` as the last one.
"""

from pathlib import Path
from typing import IO, TYPE_CHECKING

import msgspec

from lem.app.landing import checks_queue
from lem.kernel.errors import Refusal
from lem.model.landing import checks_line
from lem.records.base import Frozen
from lem.records.holds import Blocked
from lem.store import places, tasks

if TYPE_CHECKING:
    from lem.records.record import Record

# The words of the `blocked` hold of a task whose base is red: its `after` names the repair
# it waits for (`stages/land.md`, step 4).
BASE_RED = "the base is red"


def waited_for(state: Path) -> frozenset[str]:
    """The tasks another open task of the repository whose state folder is `state` waits for:
    the `after` of each queued task, and of each task blocked because the base is red."""
    return frozenset(
        named
        for record in tasks.every(state)
        if (named := after_of(record)) is not None
    )


def after_of(record: Record) -> str | None:
    """The task the record's task waits for, by the rule of `waited_for`."""
    task = record.task
    if task.status == "queued":
        return task.after
    hold = task.hold
    if isinstance(hold, Blocked) and hold.why == BASE_RED:
        return hold.after
    return None


def wanted(
    line: tuple[checks_line.Entry, ...], own: checks_line.Entry
) -> tuple[tuple[checks_line.Entry, ...], tuple[str, ...]]:
    """Each entry marked `wanted` when another open task of its repository waits for it, read
    now, once for each repository, and the repositories whose state does not read (the
    checkout moved or is gone): for this look their entries count as wanted by no task. The
    run's own repository that does not read refuses the run, as every step does."""
    named: dict[str, frozenset[str]] = {}
    unread: list[str] = []
    for repo in sorted({entry.repo for entry in line}):
        try:
            named[repo] = waited_for(places.workspace(Path(repo)).state)
        except Refusal:
            if repo == own.repo:
                raise
            named[repo] = frozenset()
            unread.append(repo)
    marked = tuple(
        msgspec.structs.replace(entry, wanted=entry.task in named[entry.repo])
        for entry in line
    )
    return marked, tuple(unread)


class Seen(Frozen, frozen=True, kw_only=True):
    """One look of a run: what it says, the repositories whose state did not read, and the
    run's place in the line, from 1."""

    look: checks_line.Look
    unread: tuple[str, ...] = ()
    position: int


def seen(
    stream: IO[str],
    folder: Path,
    own: checks_queue.Own,
    levels: checks_line.Levels,
    now: float,
) -> Seen:
    """One look of the run `own`, under the hold of `load.lock` (`stream`): the line now, read
    whole, and whether it starts, which writes the last start in the same hold."""
    line, unread = wanted(checks_queue.live(folder, own), own.entry)
    me = line[-1]
    look = checks_line.look(line, me, levels)
    if look.go:
        look = started(stream, me, now)
    position = checks_line.order(line).index(me) + 1
    return Seen(look=look, unread=unread, position=position)


def last_start(stream: IO[str]) -> checks_line.LastStart | None:
    """The last start under the gate that `load.lock` keeps; None for none."""
    stream.seek(0)
    try:
        return msgspec.json.decode(stream.read(), type=checks_line.LastStart)
    except msgspec.DecodeError:
        return None


def started(stream: IO[str], own: checks_line.Entry, now: float) -> checks_line.Look:
    """The run that is first and under the number starts, unless the last start was less than
    a minute ago; a start writes itself as the last one, in the same hold."""
    held = checks_line.spaced(last_start(stream), now)
    if held is not None:
        return held
    stream.seek(0)
    stream.truncate()
    began = checks_line.LastStart(at=now, task=own.task, repo=own.repo)
    stream.write(msgspec.json.encode(began).decode())
    stream.flush()
    return checks_line.Look(go=True)
