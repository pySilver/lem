"""Records for tests: a task at a fixed moment, made with the fields a test names."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import msgspec

from lem.kernel import release
from lem.records.journal.task import StateNoted
from lem.records.record import Record
from lem.records.task import Task

if TYPE_CHECKING:
    from collections.abc import Callable

MOMENT = datetime(2026, 11, 25, 10, 0, tzinfo=UTC)


def record(slug: str = "fix-the-login", **task: object) -> Record:
    """A queued task `slug`, with the task's fields `task` over the defaults."""
    made = Task(
        slug=slug, ask="fix the login", opened=MOMENT, status="queued", since=MOMENT
    )
    return Record(release=release.running(), task=msgspec.structs.replace(made, **task))


def noted(line: str) -> Callable[[Record], Record]:
    """A change that adds one state entry with `line` to a record's journal."""

    def change(before: Record) -> Record:
        entry = StateNoted(at=MOMENT, status=before.task.status, line=line)
        return msgspec.structs.replace(before, journal=(*before.journal, entry))

    return change
