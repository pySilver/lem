"""The owner's presence, `owner.json` in Lem's home folder: read by every workspace of the
machine, changed only when it changes."""

from typing import TYPE_CHECKING

import msgspec

from lem.kernel import files, folders, locks
from lem.kernel.errors import Fault
from lem.records.owner import Change, Presence

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.base import Moment

PRESENCE = "owner.json"
LOCK = "owner.lock"


def read(home: Path) -> Presence:
    """His presence; no file means he is there."""
    path = home / PRESENCE
    try:
        return msgspec.json.decode(path.read_bytes(), type=Presence)
    except FileNotFoundError:
        return Presence()
    except msgspec.DecodeError as error:
        raise Fault(f"{path} is no presence of the owner: {error}") from error


def change(home: Path, words: str | None, now: Moment, *, away: bool) -> Presence:
    """Mark the owner away or back with his words; a mark that changes nothing is not
    written, and gives the presence as it is."""
    folders.home_marked(home)
    with locks.held(home / LOCK):
        before = read(home)
        if before.away == away and (not away or before.words == words):
            return before
        changes = (*before.changes, Change(away=away, at=now, words=words))
        after = Presence(
            away=away, since=now, words=words, seen=len(changes), changes=changes
        )
        files.write_whole(
            home / PRESENCE, b"".join((msgspec.json.encode(after), b"\n"))
        )
    return after
