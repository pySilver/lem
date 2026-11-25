"""One line of `tasks/SLUG/sessions.jsonl`: a Claude Code session of a task, as the
`session-start` hook appends it (the design's part 3). A hook never writes `task.json`."""

from typing import Literal

import msgspec

from lem.records.base import Frozen, Moment, Slug

# The form of a line that this release writes; a reader skips a line of another form.
VERSION = 1


class SessionLine(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """A session started: when, from what (`startup`, `resume`, `clear`, `compact`, `fork`), its
    Claude Code id and transcript, its agterm pane, and the task it was started for. Every
    field is written, its form too."""

    version: int = msgspec.field(default=VERSION, name="v")
    at: Moment
    source: Literal["startup", "resume", "clear", "compact", "fork"]
    claude: str
    transcript: str
    pane: str | None = None
    task: Slug
