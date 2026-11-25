"""Green or not green, on a task's Overview (`board_task.verdict` on `main`): each reason a row
of its own; before a proposal, when the word comes; nothing for a task that ended with none."""

from typing import TYPE_CHECKING

from lem.board.inputs.task.cards import Verdict
from lem.board.views import marks
from lem.board.views.panel.common import closed
from lem.board.views.reasons import reasons

if TYPE_CHECKING:
    from lem.board.views.world import Seen, World

ALERT = "triangle-exclamation"
# What green means, after the word `green:`.
GREEN = marks.GREEN.replace("The", "the", 1)


def verdict(world: World, seen: Seen) -> Verdict | None:
    """Green or not green of the task of `seen`, or None."""
    record = seen.record
    proposed = record.landing.proposed if record.landing else None
    if proposed is None and closed(record.task):
        return None
    if proposed is None:
        return Verdict(
            look="quiet",
            icon="clock",
            word="not proposed yet:",
            text=(
                "green or not green comes with the proposal, after the checks and the "
                "review"
            ),
        )
    if proposed.green:
        return Verdict(look="done", icon="check", word="green:", text=GREEN)
    count = len(proposed.reasons)
    listed = reasons(record, "v", world.viewer.view, world.viewer.base)
    return Verdict(
        look="you",
        icon=ALERT,
        word=not_green(count),
        reasons=listed if count else None,
    )


def not_green(count: int) -> str:
    """`not green, for 4 reasons:`, `not green:`, or that no reason is on record."""
    if count > 1:
        return f"not green, for {count} reasons:"
    return "not green:" if count else "not green: no reason is on record"
