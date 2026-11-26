"""Which runs of the line another open task waits for (`land.waited_for` and `line_wanted` on
`main`): a task queued after it, or a task blocked because the base is red, whose `after` names
the repair it waits for. Read from each repository's records at each look, so that a task
queued after the entries were made counts at the next look; and the look itself (`gate_look`
on `main`), whose start writes itself into `load.lock` as the last one.
"""

import sys
from itertools import chain
from pathlib import Path
from typing import IO

import msgspec

from lem.app.landing import checks_queue
from lem.kernel.errors import Refusal
from lem.model.landing import checks_line
from lem.model.task import red_base
from lem.records.base import Frozen
from lem.store import places, survey

# The tasks waited for, and what did not read.
type Read = tuple[frozenset[str], tuple[str, ...]]


def waited_for(state: Path) -> Read:
    """The tasks another open task of the repository whose state folder is `state` waits for:
    the `after` of each queued task, and of each task blocked because the base is red; and
    the folder of each task whose record does not read, which waits for none."""
    records, unread = survey.records(state)
    waits = map(red_base.after_of, records)
    folders = [state / "tasks" / slug for slug in unread]
    return frozenset(chain.from_iterable(waits)), tuple(map(str, folders))


def wanted(
    line: tuple[checks_line.Entry, ...], own: checks_line.Entry
) -> tuple[tuple[checks_line.Entry, ...], tuple[str, ...]]:
    """Each entry marked `wanted` when another open task of its repository waits for it, read
    now, once for each repository, and what did not read: a repository whose state does not
    (the checkout moved or is gone), whose entries count as wanted by no task for this look,
    and the folder of a task whose record does not, which waits for no task. The run's own
    repository that does not read refuses the run, as every step does."""
    unread: list[str] = []
    repos = sorted({entry.repo for entry in line})
    named = {repo: read_of(repo, own, unread) for repo in repos}
    marked = tuple(
        msgspec.structs.replace(entry, wanted=entry.task in named[entry.repo])
        for entry in line
    )
    return marked, tuple(unread)


def read_of(repo: str, own: checks_line.Entry, unread: list[str]) -> frozenset[str]:
    """What the tasks of `repo` wait for; what of it did not read goes into `unread`: the
    repository, or the folder of each task whose record does not read."""
    try:
        found, left = waited_for(places.workspace(Path(repo)).state)
    except Refusal:
        if repo == own.repo:
            raise
        unread.append(repo)
        return frozenset()
    unread.extend(left)
    return found


class Seen(Frozen, frozen=True, kw_only=True):
    """One look of a run: what it says, the repositories whose state did not read, and the
    run's place in the line, from 1."""

    look: checks_line.Look
    unread: tuple[str, ...] = ()
    position: int

    def admitted(self) -> None:
        """Name on standard error each state or task folder that the look which lets the run
        start did not read: its landings counted as wanted by no task."""
        for place in self.unread:
            sys.stderr.write(
                f"Lem omitted {place} at the load gate: it does not read, so its "
                "landings counted as wanted by no task.\n"
            )


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
