"""The five tabs of a task's panel (`board_task.tab_nav` on `main`): each a link with its key on
the keyboard, the one its address shows, and the count of the documents on Artifacts."""

from typing import TYPE_CHECKING

from lem.board.inputs.names import task_href
from lem.board.inputs.task.head import Tab

if TYPE_CHECKING:
    from lem.board.views.world import World

TABS = (
    ("overview", "Overview"),
    ("criteria", "Criteria and decisions"),
    ("checks", "Checks and review"),
    ("timeline", "Timeline"),
    ("artifacts", "Artifacts"),
)


def tabs(world: World, slug: str, current: str, count: int) -> tuple[Tab, ...]:
    """The tabs of task `slug`, `current` the one shown ("" on a step of an act), `count`
    the documents Artifacts lists."""
    base, under = world.viewer.base, world.viewer.view
    return tuple(
        Tab(
            key=key,
            name=name,
            href=task_href(base, slug, None if key == "overview" else key, under),
            kbd=str(number),
            current=key == current,
            count=count if key == "artifacts" and count else None,
        )
        for number, (key, name) in enumerate(TABS, 1)
    )
