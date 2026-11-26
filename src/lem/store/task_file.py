"""Read a task file and name the files that a workspace scan reads."""

from typing import TYPE_CHECKING

import msgspec

from lem.kernel.errors import Fault, Refusal
from lem.records.record import Record
from lem.store import guard, places

if TYPE_CHECKING:
    from pathlib import Path

RECORD = "task.json"


def paths(state: Path) -> list[Path]:
    """The published record paths, by task folder."""
    guard.readable(state)
    try:
        folders = sorted((state / "tasks").iterdir())
    except FileNotFoundError:
        return []
    records = (folder / RECORD for folder in folders)
    return list(filter(published, records))


def published(path: Path) -> bool:
    """Include a record unless its path proves that no file was published."""
    try:
        path.lstat()
    except FileNotFoundError, NotADirectoryError:
        return False
    except OSError:
        return True
    return True


def read(path: Path) -> Record:
    """Read the record from its own folder."""
    body = path.read_bytes()
    try:
        record = msgspec.json.decode(body, type=Record)
    except msgspec.DecodeError as error:
        raise Fault(f"{path} is no task record: {error}") from error
    slug = path.parent.name
    named = record.task.slug
    if named != slug or not places.SLUG.fullmatch(slug):
        raise Fault(f"{path} is no task record for {slug}: it names {named}")
    return record


def required(path: Path) -> Record:
    """Refuse a decision that needs this record when the file does not read."""
    try:
        return read(path)
    except (Fault, OSError) as error:
        raise Refusal(
            "unread-task-record",
            f"Lem needs every task record for this step. It cannot read {path}.",
            f"The owner restores {path} and tries again.",
        ) from error
