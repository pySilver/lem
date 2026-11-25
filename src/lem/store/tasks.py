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

from lem.kernel import files, locks, release
from lem.kernel.errors import Fault, Refusal
from lem.records.record import SCHEMA, Record
from lem.store import guard, places

if TYPE_CHECKING:
    from pathlib import Path

RECORD = "task.json"
LOCK = "task.lock"

type Change = Callable[[Record], Record]


def encode(record: Record) -> bytes:
    """A record as its file holds it: JSON with two spaces of indent, and a line end. A record
    this release would not read back (an abbreviated commit, a time with no zone) is a fault,
    never a file."""
    formatted = msgspec.json.format(msgspec.json.encode(record), indent=2)
    try:
        msgspec.json.decode(formatted, type=Record)
    except msgspec.ValidationError as error:
        slug = record.task.slug
        raise Fault(f"the record of {slug} would not read back: {error}") from error
    return b"".join((formatted, b"\n"))


def writable(record: Record, running: str) -> None:
    """Refuse a write of a record that a newer form or a newer release wrote: the write would
    drop what this release does not know."""
    slug = record.task.slug
    if record.schema != SCHEMA:
        raise Refusal(
            "record-form",
            f"the record of {slug} is of form {record.schema}, and this Lem writes form "
            f"{SCHEMA}",
            "the owner updates Lem, then runs the command again",
        )
    if release.newer(record.release, running):
        raise Refusal(
            "newer-release",
            f"{slug} began on Lem {record.release}, which is newer than this Lem, {running}",
            "the owner updates Lem, then runs the command again",
        )


def read(state: Path, slug: str) -> Record:
    """The record of `slug`; refused when the task does not exist, a fault when the file is no
    record."""
    guard.readable(state)
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
    guard.writable(state)
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
    refused when another write came first, or when the record is of a newer form or release."""
    folder = places.task_folder(state, slug)
    guard.writable(state)
    with locks.held(folder / LOCK):
        record = read(state, slug)
        writable(record, release.running())
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
    guard.readable(state)
    folder = state / "tasks"
    if not folder.is_dir():
        return ()
    paths = folder.glob(f"*/{RECORD}")
    slugs = sorted(path.parent.name for path in paths)
    return tuple(read(state, slug) for slug in slugs)
