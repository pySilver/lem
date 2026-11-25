"""A decision taken, by an agent, a level of the ladder or the owner, as one row that opens
(`board_task.decision_row` on `main`): closed, its mark, what was chosen and by whom; opened, its
story and its chart, then what it was, why it is important, who took it and how, the ladder, the
personas and what undoes it. An important one is open at first."""

from typing import TYPE_CHECKING

from lem.board.inputs.clock import stamp
from lem.board.inputs.task.decisions import Decision, Part
from lem.board.views.artifacts.documents import chart
from lem.board.views.criteria import says
from lem.board.views.criteria.story import story_of
from lem.board.views.words import capital

if TYPE_CHECKING:
    from lem.board.inputs.parts import Document
    from lem.board.views.world import Seen, World
    from lem.records.decisions import Taken


def parts_of(
    taken: Taken, why: str | None, how: str, *, told: bool
) -> tuple[Part, ...]:
    """The parts of the opened row; who took it is in a story that tells, with the options."""
    found = (
        Part(label="The decision", text=taken.what),
        Part(label="Important", text=capital(why)) if why else None,
        None if told else Part(label="Who took it", text=capital(how)),
        Part(label="The ladder", lines=says.levels(taken)) if taken.levels else None,
        Part(label="The personas", text=taken.said) if taken.said else None,
        Part(label="To undo", text=taken.undo) if taken.undo else None,
    )
    return tuple(part for part in found if part is not None)


def drawn(seen: Seen, taken: Taken) -> Document | None:
    """The decision's chart, or None."""
    if not taken.chart:
        return None
    slug = seen.record.task.slug
    return chart(f"dec-{slug}-{taken.id}", taken.chart)


def decision_of(world: World, seen: Seen, taken: Taken) -> Decision:
    """The row of the decision `taken`."""
    why = says.importance(seen.record, taken)
    how, who = says.how_who(taken)
    story = story_of(taken, how)
    when = stamp(taken.at, world.clock.now, world.clock.zone)
    return Decision(
        id=taken.id,
        look="you" if why else "done",
        important=capital(why) if why else None,
        mark="important" if why else None,
        what=taken.what,
        chose=taken.chose,
        who=f"{who} · {when}",
        story=story,
        chart=drawn(seen, taken),
        parts=parts_of(taken, why, how, told=story is not None),
    )
