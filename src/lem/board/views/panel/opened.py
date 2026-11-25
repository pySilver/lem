"""What a task's panel is drawn with beyond the world and the task's name: the other views'
tabs (`Sections`), what the address of a step names (`Opened`), and the task as every part of
the panel reads it (`Shown`)."""

from typing import TYPE_CHECKING, NamedTuple

from lem.board.views.panel.confirm import Asked

if TYPE_CHECKING:
    from collections.abc import Callable

    from lem.board.inputs.task.artifacts import Artifacts
    from lem.board.inputs.task.checks import Checks
    from lem.board.inputs.task.decisions import Criteria
    from lem.board.inputs.task.timeline import Timeline
    from lem.board.views.standing import Standing
    from lem.board.views.world import Seen, World
    from lem.model.owner.looks import Rows


class Sections(NamedTuple):
    """The other views' tabs of a task, each a function of the world and the task."""

    criteria: Callable[[World, Seen], Criteria] | None = None
    checks: Callable[[World, Seen], Checks] | None = None
    timeline: Callable[[World, Seen], Timeline] | None = None
    artifacts: Callable[[World, Seen], Artifacts] | None = None


class Opened(NamedTuple):
    """What the address of a step names beyond its tab: the card's page, the question its
    row answered and the note typed so far; and the days a pruned task's folder kept
    everything (`state.keep_days`, None while the settings do not read)."""

    page: str | None = None
    asked: Asked = Asked()
    keep_days: int | None = None


class Shown(NamedTuple):
    """The task as the panel reads it: the world, the task, its rows of what waits for the
    owner, and where it stands."""

    world: World
    seen: Seen
    rows: Rows
    standing: Standing


NO_SECTIONS = Sections()
NOTHING_OPENED = Opened()
