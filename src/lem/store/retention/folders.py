"""The folders of the state folder whose old entries go whole (`project.PRUNED` on `main`): a
question to the experts and a panel (folders named by their day, dated by their last write), a
nap (dated by the time in its name), and the cast's copies (dated by their last write: the cast
writes the time of each read on its copy, so a copy that a panel reads stays).
"""

import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal

from lem.records.base import Frozen, Moment
from lem.store.retention.trees import newest_write, tree

if TYPE_CHECKING:
    from pathlib import Path

    from lem.store.retention.files import Removal

type Kind = Literal["experts", "panels", "naps", "cast"]
# How an entry is dated: by the time in its name (a nap), by its last write as a folder named by
# its day, or by its last write alone.
type Dated = Literal["named", "day", "written"]

CAST: Kind = "cast"
WRITTEN: Dated = "written"
DAY: Dated = "day"
PRUNED: tuple[tuple[Kind, str, Dated], ...] = (
    ("experts", "experts", DAY),
    ("panels", "panels", DAY),
    ("naps", "naps", "named"),
    (CAST, "personas-cast", WRITTEN),
    (CAST, "personas-profile", WRITTEN),
    (CAST, "personas-person", WRITTEN),
)
DAY_NAME = re.compile(r"\d{4}-\d{2}-\d{2}-.+")
NAP_NAME = re.compile(r"(?P<time>\d{4}-\d{2}-\d{2}-\d{4})(?:-.+)?")
NAP_TIME = "%Y-%m-%d-%H%M"


class Folder(Frozen, frozen=True, kw_only=True):
    """An old entry that went whole: its kind, its path in the state folder, its last moment,
    and its bytes."""

    kind: Kind
    path: str
    last: Moment
    bytes: int


def last_of(entry: Path, dated: Dated) -> datetime | None:
    """The moment an entry is dated by; None for an entry that is not one of its folder's."""
    if dated == WRITTEN:
        return newest_write(entry)
    if not entry.is_dir():
        return None
    if dated == DAY:
        return newest_write(entry) if DAY_NAME.fullmatch(entry.name) else None
    return nap_time(entry.name)


def nap_time(name: str) -> datetime | None:
    """The UTC time in a nap's name, if it names a calendar date."""
    found = NAP_NAME.fullmatch(name)
    if found is None:
        return None
    try:
        return datetime.strptime(found["time"], NAP_TIME).replace(tzinfo=UTC)
    except ValueError:
        return None


def entries_of(removal: Removal, top: Path) -> list[Path]:
    """The entries of one folder that may go: no hidden file, no lock and no link."""
    if removal.link(top) or not top.is_dir():
        return []
    names = sorted(top.iterdir())
    shown = [one for one in names if not one.name.startswith(".")]
    unlocked = [one for one in shown if not one.name.endswith(".lock")]
    return [one for one in unlocked if not removal.link(one)]


def old_folders(removal: Removal, cutoff: datetime) -> tuple[Folder, ...]:
    """Remove each entry of PRUNED older than `cutoff`."""
    gone: list[Folder] = []
    for kind, name, dated in PRUNED:
        entries = entries_of(removal, removal.top / name)
        gone.extend(old_of(removal, kind, entries, dated, cutoff))
    return tuple(gone)


def old_of(
    removal: Removal, kind: Kind, entries: list[Path], dated: Dated, cutoff: datetime
) -> list[Folder]:
    """Remove each of `entries` older than `cutoff`."""
    gone: list[Folder] = []
    for entry in entries:
        last = last_of(entry, dated)
        if last is not None and last <= cutoff:
            gone.append(went(removal, kind, entry, last))
    return gone


def went(removal: Removal, kind: Kind, entry: Path, last: datetime) -> Folder:
    """Remove the old entry whole, and what it was."""
    path = entry.relative_to(removal.top).as_posix()
    return Folder(kind=kind, path=path, last=last, bytes=tree(removal, entry))
