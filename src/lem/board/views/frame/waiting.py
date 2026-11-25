"""What waits for the owner in the sidebar (`board_pages.wait_row` on `main`): one row for each
task, its first thing's verb, look and time, how many things when two or more, and a hover that
says where he answers."""

from typing import TYPE_CHECKING

from lem.board.inputs import clock, names
from lem.board.inputs.sidebar import Waiting
from lem.board.views import owed, where
from lem.board.views.waits import facts, kinds, rows

if TYPE_CHECKING:
    from lem.board.views.world import World
    from lem.model.owner.looks import Rows


def waiting(world: World, stacks: tuple[Rows, ...]) -> tuple[Waiting, ...]:
    """One row for each task with something the owner does, in the place of its first
    thing."""
    return tuple(row_of(world, group) for group in stacks)


def row_of(world: World, group: Rows) -> Waiting:
    """The row of one task: its first thing, and how many."""
    row = group[0]
    seen = owed.seen(world, row.task)
    said = kinds.said(seen, row)
    verb = rows.verb_of(seen, row)
    return Waiting(
        id=f"w-{kinds.key_of(seen, row)}",
        slug=row.task,
        look=said.look,
        icon=said.icon,
        verb=verb,
        since=clock.since(row.since, world.clock.now, said.note),
        task=names.title_of(row.task),
        things=len(group),
        href=rows.href_of(world, seen, row, world.viewer.view),
        title=hover(world, group, verb),
        selected=row.task == world.viewer.task,
    )


def hover(world: World, group: Rows, verb: str) -> str:
    """The row's hover: its verb and task, a breaker's what, where he answers, and how many
    things of the task wait."""
    row = group[0]
    seen = owed.seen(world, row.task)
    lines = [f"{verb} · {names.title_of(row.task)}"]
    if row.kind == "breaker":
        what = facts.facts(world, seen, row, verb).what
        lines.extend([what] if what else [])
    lines.append(f"Where you answer: {where.where(seen, row)}")
    if len(group) > 1:
        things = names.plural(len(group), "thing")
        lines.append(f"{things} of this task wait for you: Waits for you lists each")
    return "\n".join(lines)
