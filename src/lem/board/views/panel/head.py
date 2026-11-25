"""The header of a task's panel (`board_task.head`, `pill`, `key_line` and `head_acts` on
`main`): its status with its time, its title, the one line it keeps when it folds, the owner's
acts, what was asked, its facts and its chips."""

from typing import TYPE_CHECKING

from lem.board.inputs import clock
from lem.board.inputs.names import title_of
from lem.board.inputs.task.head import Pill, TaskHead
from lem.board.views.panel import acts, common, facts, keyline, shown, tags

if TYPE_CHECKING:
    from lem.board.views.standing import Standing
    from lem.board.views.world import Seen, World
    from lem.model.owner.looks import Rows


def head(
    world: World, seen: Seen, rows: Rows, standing: Standing, *, acting: bool
) -> TaskHead:
    """The header of the task of `seen`; `acting` false on a step of an act, which draws no
    act of its own."""
    task = seen.record.task
    title = title_of(task.slug)
    ask = None if flat(task.ask) == flat(title) else task.ask
    return TaskHead(
        slug=task.slug,
        back=shown.view_href(world.viewer.base, world.viewer.view),
        pill=pill(world, seen, standing),
        title=title,
        key_line=keyline.key_line(seen, rows),
        acts=acts.head_acts(world, seen) if acting else None,
        ask=ask,
        facts=facts.facts(world, seen, rows, standing),
        chips=tags.tags(seen, rows),
    )


def flat(text: str) -> str:
    """A text with its spaces made one and its case dropped, to tell an ask from its title."""
    return " ".join(text.split()).casefold()


def pill(world: World, seen: Seen, standing: Standing) -> Pill:
    """The status, and how long it is in it; for a task that ended, how long ago."""
    now = world.clock.now
    ended = common.closed(seen.record.task)
    when = clock.gone if ended else clock.since
    return Pill(
        look=standing.look,
        label=standing.label,
        live=standing.live,
        since=when(standing.since, now),
    )
