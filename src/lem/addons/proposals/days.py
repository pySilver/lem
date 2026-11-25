"""The records of the proposals in the state folder: one file a day for each kind, read whole and
checked, written whole, and the one lock over them and the reviewer's items.

The lock, `proposals.lock`, is held by add, verdict and drop over their read and their write, so
that two writers at one moment (a retro while the reviewer writes his verdicts, a drop from the
board) never lose a write. A record that does not read is refused with its form: a reviewer that
read half of it would judge again what was judged, or miss what was not.
"""

import datetime as dt
from types import MappingProxyType
from typing import TYPE_CHECKING

import msgspec

from lem.addons.proposals import form, refusals
from lem.addons.proposals.record import DayRecord, Kind
from lem.kernel import files, locks

if TYPE_CHECKING:
    from contextlib import AbstractContextManager
    from io import TextIOWrapper
    from pathlib import Path

# The folder of each kind of run in the state folder.
FOLDERS: MappingProxyType[Kind, str] = MappingProxyType(
    {"night": "night", "retro": "retros"}
)
LOCK = "proposals.lock"

type Found = tuple[Kind, Path, DayRecord]


def path_of(state: Path, kind: Kind, day: dt.date) -> Path:
    """The record of `kind`'s proposals of `day`."""
    return state / FOLDERS[kind] / f"{day.isoformat()}.json"


def read(path: Path, kind: Kind) -> DayRecord | None:
    """The record at `path`, checked; None when there is no such file."""
    try:
        body = path.read_bytes()
    except FileNotFoundError:
        return None
    day = dt.date.fromisoformat(path.stem)
    try:
        record = msgspec.json.decode(body, type=DayRecord)
    except msgspec.DecodeError as error:
        raise refusals.unreadable(path, f"it does not read ({error})") from error
    said = form.problem(record, kind, day)
    if said is not None:
        raise refusals.unreadable(path, said)
    return record


def write(path: Path, record: DayRecord) -> None:
    """Write `record` whole at `path`, its folder made when it is not there."""
    path.parent.mkdir(parents=True, exist_ok=True)
    formatted = msgspec.json.format(msgspec.json.encode(record), indent=2)
    files.write_whole(path, b"".join((formatted, b"\n")))


def every(state: Path) -> tuple[Found, ...]:
    """Every record of the state folder, the night's and the retro's, oldest day first."""
    found: list[Found] = []
    for kind, folder in FOLDERS.items():
        for path in sorted((state / folder).glob("*.json")):
            record = read(path, kind) if dated(path) else None
            if record is None:
                raise refusals.unreadable(
                    path, "a record is named by its day, YYYY-MM-DD.json"
                )
            found.append((kind, path, record))
    return tuple(sorted(found, key=day_and_kind))


def day_and_kind(found: Found) -> tuple[dt.date, str]:
    """The order of the records: by day, then by kind."""
    kind, _, record = found
    return record.date, kind


def dated(path: Path) -> bool:
    """Whether the file's name is a day."""
    try:
        return dt.date.fromisoformat(path.stem).isoformat() == path.stem
    except ValueError:
        return False


def held(state: Path) -> AbstractContextManager[TextIOWrapper]:
    """The lock of the records and the reviewer's items, held while the block runs."""
    return locks.held(state / LOCK)
