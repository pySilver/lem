"""Read a task file and name the files that a workspace scan reads."""

from typing import TYPE_CHECKING

import msgspec

from lem.kernel.errors import Fault, Refusal
from lem.records.record import Record
from lem.store import guard, places

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

RECORD = "task.json"


def paths(state: Path) -> list[Path]:
    """The record path of each task folder that holds a task, published or damaged; refused
    when Lem cannot list the tasks folder, which is no empty workspace."""
    guard.readable(state)
    folder = state / "tasks"
    try:
        folders = sorted(folder.iterdir())
    except FileNotFoundError:
        return []
    except OSError as error:
        why = error.strerror or str(error)
        raise Refusal(
            "unread-task-record",
            f"Lem needs every task record for this step. It cannot list {folder}: {why}.",
            f"The owner restores read access to {folder} and tries again.",
        ) from error
    records = (one / RECORD for one in folders if places.SLUG.fullmatch(one.name))
    return list(filter(published, records))


def published(path: Path) -> bool:
    """Whether the folder of `path` holds a task: a file at the record path, or any file
    beside it but the lock and the temporary file its first write leaves (`tasks.create`).
    A folder Lem cannot look into holds one, so that its read names it."""
    try:
        path.lstat()
    except FileNotFoundError, NotADirectoryError:
        return left_files(path.parent)
    except OSError:
        return True
    return True


def left_files(folder: Path) -> bool:
    """Whether a task folder with no record still holds the files of a task."""
    try:
        names = [entry.name for entry in folder.iterdir()]
    except FileNotFoundError, NotADirectoryError:
        return False
    except OSError:
        return True
    return any(not before_first_record(name) for name in names)


def before_first_record(name: str) -> bool:
    """A file the first write of a record leaves when it is cut off: a lock, or the
    temporary file of `files.write_whole`."""
    return name.endswith(".lock") or name.startswith(f".{RECORD}.")


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
            f"Lem cannot read the task record {path}, and this step needs it.",
            f"The owner restores {path} and tries again.",
        ) from error


def named(state: Path, slugs: Iterable[str]) -> tuple[Record, ...]:
    """The records of the tasks `slugs` names that exist, for a decision about one task that
    reads only the tasks it names; refused when one of them does not read."""
    valid: list[str] = []
    for name in slugs:
        if places.SLUG.fullmatch(name) and name not in valid:
            valid.append(name)
    paths = (places.task_folder(state, slug) / RECORD for slug in valid)
    return tuple(map(required, filter(published, paths)))
