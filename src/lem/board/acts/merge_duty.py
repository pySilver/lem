"""The server's record of the other approvals when the owner's call reaches the forge."""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.sessions.here import bound
from lem.board.duties import context, merge_count
from lem.board.duties.memory import MEMORY

if TYPE_CHECKING:
    from lem.app.landing.merge_called import BeforeCall
    from lem.board.acts.asked import Asked


def counter(asked: Asked) -> BeforeCall:
    """Count at the forge call under the landing's locks."""
    duty = context.Duty(
        name=asked.checkout.name,
        here=bound(asked.checkout),
        now=asked.now,
        kept=MEMORY.of(asked.checkout),
    )
    return partial(merge_count.at_call, duty, asked.slug)
