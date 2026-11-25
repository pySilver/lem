"""What every step of an act of the owner shares (`board_task.not_now`, `act_back` and
`confirm_card` on `main`): the step with nothing to do now, the way back to the task, and the
words a page that may not act shows in the form's place; and what the request names of a step
(the question its row answered, and the note typed so far)."""

from typing import TYPE_CHECKING, NamedTuple

from lem.board.inputs.names import task_href
from lem.board.inputs.parts import Link
from lem.board.inputs.task.steps import NotNow

if TYPE_CHECKING:
    from lem.board.views.world import World


class Asked(NamedTuple):
    """What a step's address names: the key of the question its row answered (`?key=`), and
    the note the owner typed in the row (`?words=`)."""

    key: str | None = None
    words: str = ""


def back(world: World, slug: str, label: str = "Back") -> Link:
    """The way back to the task's Overview, in its panel."""
    href = task_href(world.viewer.base, slug, under=world.viewer.view)
    return Link(href=href, label=label, frame=True)


def not_now(
    world: World,
    slug: str,
    said: str,
    *,
    card: str = "confirm",
    keep: str | None = None,
) -> NotNow:
    """A step with nothing to do now: what it says, and the way back to the task."""
    link = back(world, slug, "Back to the task")
    return NotNow(id=card, said=said, back=link, keep=keep)


def act_href(world: World, slug: str, act: str) -> str:
    """Where an act of the task posts."""
    return f"{task_href(world.viewer.base, slug)}/{act}"


def under_field(world: World) -> tuple[tuple[str, str], ...]:
    """The view under the panel, as a hidden field; none over the kanban."""
    view = world.viewer.view
    return () if view == "tasks" else (("in", view),)
