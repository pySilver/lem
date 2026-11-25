"""What the card Where the time went is drawn from, before a place is a percent: the lanes of who
held the work (`ROWS` on `main`), a stretch one lane held, a moment on a lane, and a stage of the
task drawn behind every lane.

Each lane's color repeats a hue of lem.css and never stands alone: each lane has its name, and
each mark its hover.
"""

from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from datetime import datetime


class Lane(NamedTuple):
    """A lane: its key, its name and its color."""

    key: str
    label: str
    fill: str


YOU = "you"
LEM = "lem"
LEAD = "lead"
BUILDERS = "builders"
PERSONAS = "personas"
CHECKS = "checks"
REVIEW = "review"
MERGER = "merger"
LANES = (
    Lane(YOU, "You", "var(--you)"),
    Lane(LEM, "Lem", "var(--lem)"),
    Lane(LEAD, "The agent", "var(--lead)"),
    Lane(BUILDERS, "The builders", "color-mix(in srgb, var(--lead) 55%, var(--fg))"),
    Lane(PERSONAS, "The personas", "var(--quiet)"),
    Lane(CHECKS, "The checks", "var(--gate)"),
    Lane(REVIEW, "The review", "color-mix(in srgb, var(--gate) 55%, var(--fg))"),
    Lane(MERGER, "The merge agent", "color-mix(in srgb, var(--you) 55%, var(--fg))"),
)


class Held(NamedTuple):
    """A stretch a lane held the work: its lane, when it began and ended, its head and the line
    under it, and whether it runs now (it ends at the drawing's end)."""

    lane: str
    start: datetime
    end: datetime
    head: str
    sub: str = ""
    live: bool = False


class Moment(NamedTuple):
    """A moment on a lane: its lane, when, its head and the line under it."""

    lane: str
    at: datetime
    head: str
    sub: str = ""


class Stage(NamedTuple):
    """A stage of the task: its key, its name and short name, the line under it, when it began
    and ended, and whether it runs now."""

    key: str
    label: str
    short: str
    start: datetime
    end: datetime
    sub: str = ""
    live: bool = False
