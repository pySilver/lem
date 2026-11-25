"""The map of a task's files (`artifacts.arrange` on `main`): the seven sections, always all of
them, each with its documents and each document with what hangs on it (its records, the pictures
it shows), and the working files by their folder.

A record whose document is not listed, and a picture that no document shows, is a working file.
"""

from collections.abc import Mapping

from msgspec.structs import replace

from lem.board.views.artifacts.mapped import Entry, Hung, Map, Shelf
from lem.board.views.artifacts.spots import MEDIA_FOLDER, SECTIONS
from lem.board.views.artifacts.work import RECORD, piles, worked

type Entries = tuple[Entry, ...]
type Shows = Mapping[str, tuple[str, ...]]
# The document each file hangs on, by the file's path.
type Hangs = dict[str, str]


def owners(entries: Entries, shows: Shows) -> Hangs:
    """The document each entry hangs on: a picture on the first document that shows it, a
    record on its document when that is listed."""
    listed = frozenset(entry.path for entry in entries)
    hung = dict(reversed(pictures_of(shows, listed)))
    hung.update(records_of(entries, listed))
    return {path: owner for path, owner in hung.items() if path in listed}


def pictures_of(shows: Shows, listed: frozenset[str]) -> list[tuple[str, str]]:
    """Each picture a listed document's text names, with the document, in order."""
    found: list[tuple[str, str]] = []
    for doc in filter(listed.__contains__, shows):
        found.extend((picture, doc) for picture in shows[doc])
    return found


def records_of(entries: Entries, listed: frozenset[str]) -> list[tuple[str, str]]:
    """Each record whose document is listed, with that document."""
    found: list[tuple[str, str]] = []
    for entry in entries:
        doc = entry.spot.of or ""
        if entry.spot.role == RECORD and doc in listed:
            found.append((entry.path, doc))
    return found


def arrange(entries: Entries, shows: Shows) -> Map:
    """The map of `entries`, in their order; `shows` gives the pictures each document's text
    names, by the document's path."""
    hung = owners(entries, shows)
    free = tuple(entry for entry in entries if entry.path not in hung)
    docs = tuple(entry for entry in free if entry.spot.role == "doc")
    work = tuple(worked(entry) for entry in free if entry not in docs)
    return Map(
        sections=tuple(shelf(docs, hung, entries, section) for section in SECTIONS),
        work=piles(work),
        count=len(docs),
        work_count=len(work),
    )


def shelf(
    docs: Entries, hung: Hangs, entries: Entries, section: tuple[str, str]
) -> Shelf:
    """The section of key and name `section`: its documents, each with what hangs on it in
    the entries' order."""
    key, name = section
    found = (doc for doc in docs if doc.spot.group == key)
    hung_docs = tuple(hang(doc, hung, entries) for doc in found)
    return Shelf(key=key, name=name, docs=hung_docs)


def hang(doc: Entry, hung: Hangs, entries: Entries) -> Hung:
    """A document with what hangs on it: a record with its own word, a picture by its name."""
    found = (entry for entry in entries if hung.get(entry.path) == doc.path)
    return Hung(doc=doc, attached=tuple(labeled(entry) for entry in found))


def labeled(entry: Entry) -> Entry:
    """A file as it hangs on its document: a record with its own word, a picture by its
    name."""
    if entry.spot.role == RECORD:
        return entry
    return replace(entry, label=entry.path.removeprefix(MEDIA_FOLDER))
