"""The working files of a task's map, by their folder: an agent's scratch, the review tool's
archive of each round, a record with no document (in `Records with no document`), a picture no
document shows, and every file the map does not know."""

from msgspec.structs import replace

from lem.board.views.artifacts.mapped import Entry, Pile

ORPHANS = "Records with no document"
RECORD = "record"


def worked(entry: Entry) -> Entry:
    """A working file with its folder: a record with no document in its own."""
    if entry.spot.folder or entry.spot.role != RECORD:
        return entry
    return replace(entry, spot=replace(entry.spot, folder=ORPHANS))


def piles(work: tuple[Entry, ...]) -> tuple[Pile, ...]:
    """The working files by folder: those at the top first, then each folder by its name."""
    names = sorted({entry.spot.folder or "" for entry in work})
    return tuple(pile(name or None, work) for name in names)


def pile(name: str | None, work: tuple[Entry, ...]) -> Pile:
    """The working files of the folder `name`."""
    return Pile(
        folder=name, files=tuple(one for one in work if one.spot.folder == name)
    )
