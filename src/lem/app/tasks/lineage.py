"""The tasks a resumed task came from, read one at a time: the search for its plan reads an
older task only when the newer ones have none, so a damaged record of another task never stops
it (decision 30)."""

from typing import TYPE_CHECKING

from lem.store import task_file

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from lem.records.record import Record


def lineage(state: Path, record: Record) -> Iterator[str]:
    """The task, then each task it was resumed from, the nearest first; each record is read
    only when the search reaches it, and refused when it does not read."""
    slug = record.task.slug
    yield slug
    seen = {slug}
    here = record.task.resumed_from
    while here is not None and here not in seen:
        yield here
        seen.add(here)
        found = task_file.named(state, (here,))
        here = found[0].task.resumed_from if found else None
