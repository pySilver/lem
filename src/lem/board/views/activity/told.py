"""One thing that happened to a task as the feed says it (`board_model.describe` on `main`): its
look and icon, its head in bold, its text, the line under it, and whether its text is a
command, which the page prints in monospace."""

from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from lem.board.inputs.text import Look

# Who acts, as the rows of the feed are colored.
YOU: Look = "you"
LEM: Look = "lem"
LEAD: Look = "lead"
GATE: Look = "gate"
DONE: Look = "done"
QUIET: Look = "quiet"
BAD: Look = "bad"
# The icon of every fault and of every step that waits for the owner's word.
ALERT = "triangle-exclamation"
# The icon of Lem's acts on the task's sessions (`main`'s `split`).
SPLIT = "table-columns"
PAGE = "file-lines"
USER = "user"
CODE = "code"
EYE = "eye"
CHECK = "check"
CLOCK = "clock"


class Told(NamedTuple):
    """An entry in the feed's words."""

    look: Look
    icon: str
    head: str
    text: str = ""
    sub: str = ""
    mono: bool = False
