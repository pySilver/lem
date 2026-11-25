"""The line of the file the tab Artifacts shows (`board_task.artifacts_tab` and `size_of` on
`main`): its path, its kind, its size and when it changed."""

from typing import TYPE_CHECKING

from lem.board.inputs.clock import stamp
from lem.board.inputs.names import plural
from lem.board.views.artifacts import kinds, landed

if TYPE_CHECKING:
    from lem.board.views.artifacts.mapped import Entry, Map
    from lem.board.views.world import Seen, World

KB = 1024
MB = KB * KB


def meta_of(world: World, seen: Seen, entry: Entry) -> str:
    """The file's line: `pr.md · markdown · 1.2 KB · changed 08:32`."""
    plan = seen.plan_file if entry.first else None
    stats = (one for one in seen.stats if one.path == entry.path)
    stat = next(stats, None) if plan is None else plan.stat
    parts = [entry.path, kinds.WORDS[entry.kind]]
    if stat is not None:
        changed = stamp(stat.changed, world.clock.now, world.clock.zone)
        parts.extend((size_of(stat.size), f"changed {changed}"))
    return " · ".join(parts)


def size_of(size: int) -> str:
    """A file's size as the board says it: `512 B`, `1.2 KB`, `14 KB`, `3.1 MB`."""
    if size < KB:
        return f"{size} B"
    kilo, mega = size / KB, size / MB
    if size < KB * 10:
        return f"{kilo:.1f} KB"
    if size < MB:
        return f"{kilo:.0f} KB"
    return f"{mega:.1f} MB"


def said_of(world: World, seen: Seen, found: Map) -> str:
    """The line under the map: its documents, its read and any pending pull request text."""
    pending = landed.pending(seen.record)
    if not seen.files:
        ending = pending or "."
        return f"The task has no file yet{ending}"
    now = world.clock.now
    count = plural(found.count, "document")
    read = stamp(now, now, world.clock.zone)
    return f"{count}, read {read}{pending}"
