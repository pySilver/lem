"""The waits of a run of the checks as the task keeps them: one `CheckWait` in the journal for
each change of why it waits, and `checks-wait.json`, its whole wait now, which `--status` reads.

`checks-wait.json` is a stand-in until `CheckWait` holds the whole wait (`notes/land-checks.md`):
why it goes behind the first, that one's repository, the run it waits a minute after, and the
line for the owner.
"""

from datetime import UTC, datetime
from functools import partial
from typing import TYPE_CHECKING

import msgspec

from lem.app.landing import changes
from lem.kernel import files
from lem.model.landing import checks_said
from lem.records.base import Frozen, Moment
from lem.records.journal.landing import CheckWait
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path

WAITS = "checks-wait.json"


class Waited(Frozen, frozen=True, kw_only=True):
    """`checks-wait.json`: why the run waits now, and its line for the owner, since `at`."""

    at: Moment
    wait: checks_said.Wait
    say: str


def noted(state: Path, slug: str, entry: CheckWait) -> None:
    """One wait in the task's journal."""
    record = tasks.read(state, slug)
    tasks.update(state, slug, partial(changes.noted, entry=entry), record.revision)


def moment(seconds: float) -> datetime:
    """A moment of the clock as a record holds it."""
    return datetime.fromtimestamp(seconds, UTC).replace(microsecond=0)


def told(folder: Path, slug: str, wait: checks_said.Wait, at: datetime) -> None:
    """The run's wait as `--status` reads it, in the task's folder."""
    said = Waited(at=at, wait=wait, say=checks_said.waiting(slug, wait))
    files.write_whole(folder / WAITS, msgspec.json.encode(said))


def waited(
    state: Path, slug: str, wait: checks_said.Wait, position: int, now: float
) -> None:
    """Tell a new wait: one `CheckWait` in the journal, and `checks-wait.json`."""
    at = moment(now)
    entry = CheckWait(
        at=at,
        reason="behind" if wait.behind else "load",
        load=wait.load,
        start_below=wait.start,
        behind=wait.behind,
        position=position,
    )
    noted(state, slug, entry)
    told(places.task_folder(state, slug), slug, wait, at)


def read(folder: Path) -> Waited | None:
    """The task's wait as `checks-wait.json` keeps it; None when there is none to read."""
    try:
        return msgspec.json.decode((folder / WAITS).read_bytes(), type=Waited)
    except OSError, msgspec.DecodeError:
        return None
