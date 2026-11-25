"""What the owner may do with an item of the Backlog view (`board_pages.backlog_item` on
`main`): see the task that builds it; else start a task from it, and drop a reviewer's item that
waits for him, where the page may act; else copy the line he types in a session."""

import re
from typing import TYPE_CHECKING

from lem.board.inputs.backlog import Holds
from lem.board.inputs.forms import ActForm, Field
from lem.board.inputs.names import task_href
from lem.board.inputs.parts import Link
from lem.board.views.backlog.groups import refuted
from lem.records.holds import Parked

if TYPE_CHECKING:
    from lem.board.inputs.layout import Viewer
    from lem.board.inputs.text import Href
    from lem.board.views.backlog_read import Entry
    from lem.records.record import Record

# A path a line to type keeps as it is.
SAFE_PATH = re.compile(r"^[A-Za-z0-9._/-]+$")
FIELD = "item"
HELD_REVIEWER = (
    "It leaves the backlog with that task's landing, and is undecided again when the task "
    "is dropped."
)
HELD_FOLDER = "Start a task comes back here when that task is dropped."
WAITS = (
    "Start a task opens its own session in agterm, which reads this item. Drop removes the "
    "file, and the day's record of the proposals keeps the drop, so no later reviewer "
    "proposes it again."
)
OPENS = "Lem opens the task's own session in agterm, which reads this item."
DROP_HERE = "Drop it on this board on the Mac or through the tailnet door."
BAD_NAME = (
    "The name of this file has a character that a line to type would not keep. Start the "
    "task yourself in a session, with your own words."
)


def holds_of(viewer: Viewer, entry: Entry, held: Record | None) -> Holds:
    """What the owner may do with the item `entry`, which the task `held` may build."""
    if held is not None:
        return held_holds(viewer, entry, held)
    path = entry.path
    waits = entry.reviewer and not refuted(entry)
    if viewer.may_act:
        return Holds(
            start=start(viewer.base, path),
            drop=drop(viewer.base, path) if waits else None,
            note=WAITS if waits else OPENS,
        )
    if SAFE_PATH.fullmatch(path):
        return Holds(typed=f"/lem new {path}", note=DROP_HERE if waits else None)
    return Holds(bad=BAD_NAME)


def held_holds(viewer: Viewer, entry: Entry, held: Record) -> Holds:
    """The task that builds the item, with its state, and when the item comes back."""
    task = held.task
    word = "parked" if isinstance(task.hold, Parked) else task.status
    rest = HELD_REVIEWER if entry.reviewer else HELD_FOLDER
    href = task_href(viewer.base, task.slug, under="backlog")
    return Holds(
        held_by=Link(href=href, label=task.slug, frame=True),
        held=f"({word}) builds this item. {rest}",
    )


def start(base: Href, path: str) -> ActForm:
    """The form that starts a task from the item at `path`."""
    return ActForm(
        action=f"{base}/start",
        label="Start a task",
        icon="play",
        press="go",
        busy="Starting…",
        fields=(Field(name=FIELD, shown=path),),
    )


def drop(base: Href, path: str) -> ActForm:
    """The form that drops the reviewer's item at `path`."""
    return ActForm(
        action=f"{base}/backlog/drop",
        label="Drop",
        icon="xmark",
        busy="Dropping…",
        fields=(Field(name=FIELD, shown=path),),
    )
