"""The view Activity, `/HOST/WORKSPACE/activity`: where the time of today's tasks went, as one
row for each, and every event, the newest first; and the page of a new task.

A view gives each place on a chart as a percent of its width, so that the template prints it.
"""

from lem.board.inputs.forms import ActForm
from lem.board.inputs.parts import Input, Link, When
from lem.board.inputs.text import Icon, Inline, Look, Plain


class Stretch(Input, frozen=True, kw_only=True):
    """A stretch of one status on a task's row: where it starts and how wide it is (percents),
    its status and look, whether it runs now, whether it is a dot (no length), and its hover
    (`Building · The agent · 14:09 to now · 1h 51m`)."""

    left: float
    width: float
    status: Plain
    look: Look
    live: bool = False
    dot: bool = False
    title: Plain


class Lane(Input, frozen=True, kw_only=True):
    """A task's row: its slug, the link of its title to its Timeline, and its stretches."""

    slug: Plain
    task: Link
    stretches: tuple[Stretch, ...] = ()


class Tick(Input, frozen=True, kw_only=True):
    """A label of the time axis: where it is (a percent), its clock, its date when it has one,
    and whether it is the first or the last."""

    left: float
    clock: Plain
    date: Plain | None = None
    first: bool = False
    last: bool = False


class Shade(Input, frozen=True, kw_only=True):
    """An entry of the legend: its look, the status of its swatch when it has one of its own,
    the words of its statuses (`Queued · Ready for its checks`), and its hover."""

    look: Look
    status: Plain | None = None
    label: Plain
    title: Plain


class Happened(Input, frozen=True, kw_only=True):
    """An event of the feed: its id, its look and icon, the task it is of, its head, its text
    (in monospace for a check), the line under it, and when."""

    id: Plain
    look: Look
    icon: Icon
    task: Link | None = None
    head: Plain
    text: Inline | None = None
    mono: bool = False
    sub: Inline | None = None
    at: When


class Activity(Input, frozen=True, kw_only=True):
    """The view: the day of the axis (`today`), its ticks, where the line of now is (none when
    nothing runs), the legend, the rows (none until a task writes its first state), how many
    events and whether the feed shows only the newest, and the feed."""

    day: Plain
    ticks: tuple[Tick, ...] = ()
    now: float | None = None
    shades: tuple[Shade, ...] = ()
    lanes: tuple[Lane, ...] = ()
    events: Plain
    feed: tuple[Happened, ...] = ()


class NewTask(Input, frozen=True, kw_only=True):
    """The page `/HOST/WORKSPACE/new`: the form that starts a task from the owner's words
    (none where the page may not act), and the way back to the tasks."""

    form: ActForm | None = None
    cancel: Link
