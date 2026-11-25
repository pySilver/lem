"""The tab Artifacts of a task (`board_task.artifacts_tab` on `main`): its map at the left, and
at the right the file the address names, or else its first markdown document, its first
document, or its first file. An HTML page takes the whole width.
"""

from typing import TYPE_CHECKING

from lem.board.inputs.clock import stamp
from lem.board.inputs.names import plural
from lem.board.inputs.task.artifacts import Artifacts, Shown
from lem.board.views.artifacts import kinds, meta
from lem.board.views.artifacts.addresses import raw_href
from lem.board.views.artifacts.body import body
from lem.board.views.artifacts.chosen import chosen_of
from lem.board.views.artifacts.listing import entries_of, map_of
from lem.board.views.artifacts.rows import folder_of, section_of

if TYPE_CHECKING:
    from lem.board.views.artifacts.mapped import Entry, Map
    from lem.board.views.world import Seen, World


def first_of(found: Map, entries: tuple[Entry, ...]) -> Entry | None:
    """The file shown when the address names none: the first markdown document, the first
    document, the first file."""
    docs = [hung.doc for shelf in found.sections for hung in shelf.docs]
    marked = (doc for doc in docs if doc.kind == kinds.MARKDOWN)
    first = next(marked, None) or next(iter(docs), None)
    return first or next(iter(entries), None)


def shown_of(world: World, seen: Seen, entry: Entry) -> Shown:
    """The file shown, with its line and its body; an HTML page with the way to open it
    alone."""
    wide = entry.kind == kinds.HTML and not entry.first
    alone = raw_href(world, seen.record.task.slug, entry.path) if wide else None
    return Shown(
        path=entry.path,
        title=entry.spot.title or entry.path,
        kind=entry.kind,
        icon=kinds.ICONS[entry.kind],
        meta=meta.meta_of(world, seen, entry),
        alone=alone,
        body=body(world, seen, entry),
    )


def artifacts(world: World, seen: Seen) -> Artifacts:
    """The tab Artifacts of the task `seen`."""
    entries = entries_of(seen)
    found = map_of(seen)
    chosen = chosen_of(world, seen)
    entry = next((one for one in entries if one.path == chosen), None)
    entry = entry or first_of(found, entries)
    return tabbed(world, seen, found, entry, chosen=chosen is not None)


def tabbed(
    world: World, seen: Seen, found: Map, entry: Entry | None, *, chosen: bool
) -> Artifacts:
    """The tab with the file `entry` shown, or the words in its place."""
    slug = seen.record.task.slug
    path = entry.path if entry else None
    shown = shown_of(world, seen, entry) if entry else None
    return Artifacts(
        sections=tuple(section_of(world, seen, one, path) for one in found.sections),
        work=tuple(folder_of(world, slug, pile, path) for pile in found.work),
        work_count=found.work_count,
        said=said_of(world, seen, found),
        shown=shown,
        empty=None if shown else empty_of(seen),
        chosen=chosen,
        wide=bool(chosen and shown and shown.alone),
    )


def said_of(world: World, seen: Seen, found: Map) -> str:
    """The line under the map: how many documents, and when the folder was read."""
    if not seen.files:
        return "The task has no file yet."
    now = world.clock.now
    count = plural(found.count, "document")
    read = stamp(now, now, world.clock.zone)
    return f"{count}, read {read}"


def empty_of(seen: Seen) -> str:
    """The words where no file is shown."""
    return "Pick a file at the left." if seen.files else "Nothing to show."
