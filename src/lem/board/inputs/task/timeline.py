"""The tab Timeline of a task, `/HOST/WORKSPACE/tasks/SLUG/timeline`: who held the work, drawn as
lanes over the task's time, its stretches (the build's tasks, the checks, the pull request) as
bands, and the task's events.

A view gives each place as a percent of the chart's width, and each tip the moments it spans:
the browser's tip prints them.
"""

from lem.board.inputs.activity import Happened, Tick
from lem.board.inputs.parts import Input, Moment, Note
from lem.board.inputs.task.overview import Went
from lem.board.inputs.text import Look, Plain


class Band(Input, frozen=True, kw_only=True):
    """A stretch of the task over every lane (`Task 2`, `Checks`): its id, where it starts and
    how wide it is, whether it is an odd one (its shade) or the one now, its short words (`T2`),
    the head and line of its tip, and the moments it spans (to now when it runs)."""

    id: Plain
    left: float
    width: float
    odd: bool = False
    now: bool = False
    short: Plain
    head: Plain
    sub: Plain | None = None
    start: Moment
    end: Moment | None = None


class Spell(Input, frozen=True, kw_only=True):
    """A stretch a lane held the work: its id, where it starts and how wide it is, whether it
    runs, the head and line of its tip, and the moments it spans."""

    id: Plain
    left: float
    width: float
    live: bool = False
    head: Plain
    sub: Plain | None = None
    start: Moment
    end: Moment | None = None


class Mark(Input, frozen=True, kw_only=True):
    """A moment on a lane (an answer, a move): its id, where it is, and its tip."""

    id: Plain
    left: float
    head: Plain
    sub: Plain | None = None
    at: Moment


class Track(Input, frozen=True, kw_only=True):
    """A lane (you, the lead, a builder, the checks, the review, the merge agent): its key and
    label, its color, its spells and its marks; and on the legend, how long it held the work, its
    share and the legend's hover (none for a lane that held nothing)."""

    key: Plain
    label: Plain
    fill: Plain
    spells: tuple[Spell, ...] = ()
    marks: tuple[Mark, ...] = ()
    held: Plain | None = None
    held_title: Plain | None = None


class Time(Input, frozen=True, kw_only=True):
    """The card Where the time went: its look, the task's whole time (`2h 42m in all`), what
    the shares add up to when two lanes held the same minutes, the bands, the lanes, the axis's
    day and ticks, whether a tick carries a date, and where the line of now is (none once the
    task ended)."""

    look: Look
    whole: Plain
    over: Plain | None = None
    bands: tuple[Band, ...] = ()
    tracks: tuple[Track, ...] = ()
    day: Plain
    ticks: tuple[Tick, ...] = ()
    dated: bool = False
    now: float | None = None


class Timeline(Input, frozen=True, kw_only=True):
    """The tab: the result of an act, the card of the time, the card of the events (its line
    and its rows), and what went with a pruned task's events."""

    note: Note | None = None
    time: Time | None = None
    events: Plain | None = None
    feed: tuple[Happened, ...] = ()
    went: Went | None = None
