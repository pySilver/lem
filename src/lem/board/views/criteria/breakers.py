"""A breaker as one row that opens, in the look of a decision (`board_task.breaker_row` and
`board_model.breaker_says` on `main`): what stopped the build and why, where it stands (it waits
for the owner, for nobody while the task is parked, helped by a decision of his, or the task
ended), its document and its handoff on Artifacts, and the decision that helped it. One that
waits is open at first."""

from typing import TYPE_CHECKING

from lem.board.inputs.clock import stamp
from lem.board.inputs.task.decisions import Decision, Part
from lem.board.views.criteria.links import files_of, help_link
from lem.board.views.criteria.terms import stop_words
from lem.board.views.panel.answer import breaker as answer
from lem.board.views.words import capital
from lem.records.decisions import Taken
from lem.records.holds import Parked, ReleaseHold

if TYPE_CHECKING:
    from lem.board.inputs.text import Look
    from lem.board.views.world import Seen, World
    from lem.records.decisions import Breaker

ENDED = frozenset(("landed", "answered", "dropped"))


def helper(seen: Seen, breaker: Breaker) -> int | None:
    """The number of the owner's decision that helped the breaker, or None."""
    helps = (
        one.id
        for one in seen.record.task.decisions
        if isinstance(one, Taken) and one.by == "owner" and one.breaker == breaker.id
    )
    return next(helps, None)


def standing(seen: Seen, breaker: Breaker) -> tuple[str, Look]:
    """Where the breaker stands, and who acts on it."""
    task = seen.record.task
    helped = helper(seen, breaker)
    if helped is not None:
        return f"helped by your decision {helped}", "done"
    if task.status in ENDED:
        return f"the task is {task.status}: it no longer waits", "quiet"
    if isinstance(task.hold, ReleaseHold):
        return "the release stop suspends this breaker", "quiet"
    if isinstance(task.hold, Parked):
        return (
            f"the task is parked: it waits for nobody until /lem resume {task.slug}",
            "quiet",
        )
    return "it waits for you", "you"


def parts_of(world: World, seen: Seen, breaker: Breaker, now: str) -> tuple[Part, ...]:
    """The opened row: now, its files, and where the owner answers while it waits for him."""
    helped = helper(seen, breaker)
    links = () if helped is None else (help_link(helped),)
    files = files_of(world, seen, breaker)
    waits = now == "it waits for you"
    found = (
        Part(label="Now", text=capital(now), links=links),
        Part(label="Its files", links=files) if files else None,
        Part(label="Where you answer", text=answer(seen.record.task.slug))
        if waits
        else None,
    )
    return tuple(part for part in found if part is not None)


def breaker_of(world: World, seen: Seen, breaker: Breaker) -> Decision:
    """The row of the breaker."""
    why = stop_words(breaker.cause, breaker.irreversible)
    now, look = standing(seen, breaker)
    when = stamp(breaker.at, world.clock.now, world.clock.zone)
    return Decision(
        kind="breaker",
        id=breaker.id,
        look=look,
        important=capital(why) if look == "you" else None,
        mark="breaker",
        what=breaker.what,
        chose=capital(why),
        who=f"{now} · {when}",
        parts=parts_of(world, seen, breaker, now),
    )
