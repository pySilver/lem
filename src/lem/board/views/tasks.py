"""The view Tasks (`board_pages.kanban` and `task_card` on `main`): the tasks in four columns by
who acts, each a card with its line, its time and its chips, and Done's way to the older ended
tasks it has no card for. A parked task has no card: Waits for you lists it apart."""

from typing import TYPE_CHECKING, NamedTuple

from types import MappingProxyType

from lem.board.inputs import names
from lem.board.inputs.parts import Link
from lem.board.inputs.tasks import Column, Tasks
from lem.board.views import cards, kanban_order, owed, standing

if TYPE_CHECKING:
    from lem.board.inputs.text import Look
    from lem.board.views.world import Seen, World

    # A task with where it stands.
    type Placed = tuple[Seen, standing.Standing]


class Spec(NamedTuple):
    """A column with no card: its key, look, title, and words when empty."""

    key: str
    look: Look
    title: str
    empty: str


COLUMNS = (
    Spec("you", "you", "Waits for you", "Nothing waits for you"),
    Spec("build", "lead", "Building", "No task builds"),
    Spec("checks", "gate", "Checks and review", "No branch is checked or reviewed"),
    Spec("done", "done", "Done", "Nothing landed yet"),
)
TITLES = MappingProxyType({spec.key: spec.title for spec in COLUMNS})
DONE = "done"


def tasks(world: World) -> Tasks:
    """The four columns of the world's tasks."""
    placed = placed_of(world)
    return Tasks(columns=tuple(column(world, spec, placed) for spec in COLUMNS))


def placed_of(world: World) -> list[Placed]:
    """Every task with where it stands."""
    return [
        (seen, standing.standing(seen, owed.of_task(world, seen.record.task.slug)))
        for seen in world.tasks
    ]


def column(world: World, spec: Spec, placed: list[Placed]) -> Column:
    """One column with its cards, and Done's way to the older ones."""
    mine = [pair for pair in placed if pair[1].column == spec.key]
    order = kanban_order.ordered(spec.key, mine)
    shown = order[: kanban_order.SHOWN] if spec.key == DONE else order
    return Column(
        key=spec.key,
        look=spec.look,
        title=spec.title,
        empty=spec.empty,
        folded=spec.key in world.viewer.folded,
        cards=tuple(
            cards.card(world, seen, where, TITLES[spec.key]) for seen, where in shown
        ),
        older=older_link(world, len(order) - len(shown)),
    )


def older_link(world: World, count: int) -> Link | None:
    """Done's way to the ended tasks it has no card for."""
    if count <= 0:
        return None
    older = names.plural(count, "older one")
    shown = kanban_order.SHOWN
    title = (
        f"Done shows the {shown} tasks that ended last: open the list of the {older}"
    )
    base = world.viewer.base
    return Link(
        href=f"{base}/{DONE}", label=f"{count} older", title=title, icon="clock"
    )
