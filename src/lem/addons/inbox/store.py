"""Publish the Inbox record whole, before a send and after its receipt."""

from typing import TYPE_CHECKING

import msgspec

from lem.addons.inbox.records import Record
from lem.kernel import files
from lem.kernel.errors import Fault
from lem.store import guard

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.base import Moment

RECORD = "inbox.json"
LOCK = "inbox.lock"


def read(state: Path) -> Record:
    """Read a record from this Lem's state."""
    guard.readable(state)
    try:
        return msgspec.json.decode((state / RECORD).read_bytes(), type=Record)
    except FileNotFoundError:
        return Record()
    except msgspec.DecodeError as error:
        raise Fault("the owner's Inbox record is unreadable") from error


def write(state: Path, before: Record, after: Record, now: Moment) -> Record:
    """Keep the latest change time, with no write when nothing changed."""
    if before == after:
        return before
    checked = msgspec.structs.replace(after, looked=now)
    files.write_whole(state / RECORD, msgspec.json.encode(checked))
    return checked
