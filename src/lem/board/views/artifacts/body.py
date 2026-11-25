"""The file shown on the tab Artifacts, by its kind (`board_task.art_body` on `main`): an HTML
page in a sandboxed frame, a picture of the task's media, markdown rendered, a text file as
`lines.py` shows it; why the board shows no text of it; and where the file is.

A view reads no file: the text is the one the gather read beside the record (`Seen.text`), and a
file it did not read says that the board has no text of it.
"""

from typing import TYPE_CHECKING

from lem.board.inputs.task.artifacts import Body
from lem.board.views.artifacts import kinds
from lem.board.views.artifacts.bodies import pictured, rendered
from lem.board.views.artifacts.lines import record_of, shown

if TYPE_CHECKING:
    from lem.board.views.artifacts.mapped import Entry
    from lem.board.views.world import Seen, World

UNSHOWN = frozenset((kinds.BINARY, kinds.IMAGE))


def where_of(entry: Entry) -> str:
    """Where the file is: the plan in the task's worktree, any other in its folder."""
    place = "worktree" if entry.first else "folder"
    return f"It is at {entry.path} in the task’s {place}."


def body(world: World, seen: Seen, entry: Entry) -> Body:
    """The file `entry` of the task as the tab shows it."""
    slug = seen.record.task.slug
    where = where_of(entry)
    framed = pictured(world, slug, entry)
    if framed is not None:
        return framed
    if entry.kind in UNSHOWN:
        return Body(said="A binary file: the board does not show it.", where=where)
    text = seen.plan_text if entry.first else seen.text(entry.path)
    if text is None:
        return Body(said="The board has no text of this file.", where=where)
    if entry.kind == kinds.MARKDOWN:
        return Body(document=rendered(world, seen, entry, text), where=where)
    return shown(entry.kind, text, where, record_of(world, slug, entry))
