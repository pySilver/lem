"""A task's record, `tasks/SLUG/task.json`, read and written whole (the design's part 3, "A
write").

`update` holds the record lock over its read, the check of the revision the caller read, the
pure change, and the write, and over nothing else: an effect never runs under it. A stale
revision is refused, so that of two writers that read the same record the second learns of the
first instead of writing over it.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING

import msgspec

from lem.kernel import files, locks
from lem.kernel.errors import Fault, Refusal
from lem.records.record import Record
from lem.store import places

if TYPE_CHECKING:
    from pathlib import Path

RECORD = "task.json"
LOCK = "task.lock"

type Change = Callable[[Record], Record]


def encode(record: Record) -> bytes:
    """A record as its file holds it: JSON with two spaces of indent, and a line end."""
    formatted = msgspec.json.format(msgspec.json.encode(record), indent=2)
    return b"".join((formatted, b"\n"))


def read(state: Path, slug: str) -> Record:
    """The record of `slug`; refused when the task does not exist, a fault when the file is no
    record."""
    path = places.task_folder(state, slug) / RECORD
    try:
        body = path.read_bytes()
    except FileNotFoundError:
        raise Refusal(
            "no-task", f"no task {slug} here", "lem task list names the tasks"
        ) from None
    try:
        return msgspec.json.decode(body, type=Record)
    except msgspec.DecodeError as error:
        raise Fault(f"{path} is no task record: {error}") from error


def create(state: Path, record: Record) -> Record:
    """Write the first record of a new task, at revision 1; refused when the task exists."""
    slug = record.task.slug
    folder = places.task_folder(state, slug)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / RECORD
    with locks.held(folder / LOCK):
        if path.exists():
            raise Refusal(
                "task-exists",
                f"a task {slug} is here already",
                "name the new task another way",
            )
        first = msgspec.structs.replace(record, revision=1)
        files.write_whole(path, encode(first))
    return first


def update(state: Path, slug: str, change: Change, expect: int) -> Record:
    """Apply `change` to the record at revision `expect`, and write it as the next revision;
    refused when another write came first."""
    folder = places.task_folder(state, slug)
    with locks.held(folder / LOCK):
        record = read(state, slug)
        if record.revision != expect:
            raise Refusal(
                "stale",
                f"{slug} is at revision {record.revision}, not {expect}: another write "
                "came first",
                "read the task again, and decide on what it says now",
            )
        changed = msgspec.structs.replace(change(record), revision=expect + 1)
        files.write_whole(folder / RECORD, encode(changed))
    return changed


def every(state: Path) -> tuple[Record, ...]:
    """The record of every task in `state`, by slug."""
    folder = state / "tasks"
    if not folder.is_dir():
        return ()
    paths = folder.glob(f"*/{RECORD}")
    slugs = sorted(path.parent.name for path in paths)
    return tuple(read(state, slug) for slug in slugs)
