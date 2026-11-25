"""The panel of one task, beside the view or over it: its header, its tabs, and the one tab or
step its address shows; or a task with no state yet, or no task at all."""

from typing import Literal

from lem.board.inputs.parts import Input
from lem.board.inputs.task.artifacts import Artifacts
from lem.board.inputs.task.checks import Checks
from lem.board.inputs.task.decisions import Criteria
from lem.board.inputs.task.head import Tab, TaskHead
from lem.board.inputs.task.overview import Overview
from lem.board.inputs.task.steps import Card, Drop, Merge, NotNow, Park
from lem.board.inputs.task.timeline import Timeline
from lem.board.inputs.text import Href, Plain

# What the address of a panel opens: a tab, or a step of an act.
type Shows = Literal[
    "overview",
    "criteria",
    "checks",
    "timeline",
    "artifacts",
    "merge",
    "park",
    "drop",
    "card",
]


class Missing(Input, frozen=True, kw_only=True):
    """A panel with no task of its own: its crumb (`A task`), its title, what it says (a task
    whose session wrote no state yet, or an address that names no task, tab or file), and the
    view it goes back to."""

    title: Plain
    said: Plain
    back: Href
    found: bool = False


class Panel(Input, frozen=True, kw_only=True):
    """The panel: the task's slug, what its address opens, its header and tabs, and the one tab
    or step shown; or the panel of no task."""

    slug: Plain
    shows: Shows = "overview"
    head: TaskHead | None = None
    tabs: tuple[Tab, ...] = ()
    overview: Overview | None = None
    criteria: Criteria | None = None
    checks: Checks | None = None
    timeline: Timeline | None = None
    artifacts: Artifacts | None = None
    merge: Merge | None = None
    park: Park | None = None
    drop: Drop | None = None
    card: Card | None = None
    not_now: NotNow | None = None
    missing: Missing | None = None
