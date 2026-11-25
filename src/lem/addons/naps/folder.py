"""The naps' folder, `naps/` of the state folder: one folder for each nap, named by the clock's
minute it started and a few words of its dream, and `.asleep`, the record of the newest start
that `lem nap may` writes (`project.cmd_may_nap` on `main`).

A nap runs until its folder holds `waking.md`, the last file it writes. A folder whose name holds
no time, and a link, are no nap. An old nap's folder goes with `lem prune`, never here.
"""

import datetime as dt
import re
from typing import TYPE_CHECKING, Annotated

import msgspec

from lem.kernel import files
from lem.kernel.errors import Refusal
from lem.records.base import Frozen, Moment

if TYPE_CHECKING:
    from pathlib import Path

NAPS = "naps"
ASLEEP = ".asleep"
WAKING = "waking.md"
NAME = re.compile(r"(?P<time>\d{4}-\d{2}-\d{2}-\d{4})(?:-.+)?")
TIME = "%Y-%m-%d-%H%M"

type Started = tuple[dt.datetime, str]


class Asleep(Frozen, frozen=True, kw_only=True):
    """The newest start: its moment, and the minute that names its folder."""

    since: Moment
    time: Annotated[str, msgspec.Meta(pattern=r"^\d{4}-\d{2}-\d{2}-\d{4}$")]


def started(name: str) -> dt.datetime | None:
    """When the nap of a folder named `name` started; None for a name that holds no time."""
    found = NAME.fullmatch(name)
    if found is None:
        return None
    try:
        return dt.datetime.strptime(found["time"], TIME).replace(tzinfo=dt.UTC)
    except ValueError:
        return None


def naps_of(folder: Path) -> tuple[Started, ...]:
    """Each nap of the folder, by its start, oldest first; a link and a name with no time are
    none."""
    if not folder.is_dir():
        return ()
    found = (nap_of(path) for path in folder.iterdir())
    return tuple(sorted(filter(None, found)))


def nap_of(path: Path) -> Started | None:
    """The start and name of the nap at `path`; None for a link, a file or a name with no
    time."""
    if path.is_symlink() or not path.is_dir():
        return None
    when = started(path.name)
    return None if when is None else (when, path.name)


def asleep_of(folder: Path) -> Asleep | None:
    """The record of the newest start, None with none; refused when it does not read."""
    path = folder / ASLEEP
    try:
        body = path.read_bytes()
    except FileNotFoundError:
        return None
    try:
        return msgspec.json.decode(body, type=Asleep)
    except msgspec.DecodeError as error:
        raise Refusal(
            "asleep-record",
            f"{path} is not the record lem nap may writes ({error})",
            "remove the file; the next call writes it again",
        ) from error


def fell_asleep(folder: Path, record: Asleep) -> None:
    """Write the record of a start whole, the folder made when it is not there."""
    folder.mkdir(parents=True, exist_ok=True)
    body = b"".join((msgspec.json.encode(record), b"\n"))
    files.write_whole(folder / ASLEEP, body)


def woke(folder: Path, record: Asleep, naps: tuple[Started, ...]) -> bool:
    """Whether the nap of the record wrote its waking note."""
    mine = (name for _, name in naps if name.startswith(record.time))
    return any((folder / name / WAKING).is_file() for name in mine)
