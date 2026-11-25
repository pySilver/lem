"""The pictures of a task's `media/` folder that each of its documents shows, by the paths its
text names (`artifacts.pictures_named` on `main`): such a picture hangs on that document's row,
and one that no document names is a working file."""

import re
from typing import TYPE_CHECKING

from lem.board.views.artifacts.spots import MEDIA_FOLDER

if TYPE_CHECKING:
    from lem.board.views.artifacts.mapped import Entry
    from lem.board.views.world import Seen

# A path in a document's text that names a picture of the task's media folder.
MEDIA_REF = re.compile(
    r"(?:^|[(\s\"'/])(media/[A-Za-z0-9._/-]+\.(?:png|jpe?g|gif|webp))\b", re.IGNORECASE
)
type Shows = dict[str, tuple[str, ...]]
DOC = "doc"


def shows_of(seen: Seen, entries: tuple[Entry, ...]) -> Shows:
    """The pictures of `media/` each markdown document of the folder names, by its path; none
    when the task has no picture."""
    if not any(entry.path.startswith(MEDIA_FOLDER) for entry in entries):
        return {}
    named: Shows = {}
    for entry in filter(read, entries):
        pictures = named_in(seen.text(entry.path) or "")
        if pictures:
            named[entry.path] = pictures
    return named


def read(entry: Entry) -> bool:
    """Whether a file's text is read for pictures: a document of the folder, not the plan."""
    return entry.spot.role == DOC and not entry.first


def named_in(text: str) -> tuple[str, ...]:
    """The pictures of `media/` a document's text names, each once, in order."""
    return tuple(sorted({found[1] for found in MEDIA_REF.finditer(text)}))
