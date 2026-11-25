"""His Park of a task a breaker holds, from the board (`serve.act_park` on `main`): `lem task park
SLUG --why WHY` with his one line of why, the act in the journal, and the word to its session.

The park answers the breaker's question by putting the task aside: the breaker's hold goes aside
with it, so a later answer to that question finds the task parked and says so, and his resume
gives the breaker back to answer anew (`app/tasks/park.py`).
"""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.tasks import park
from lem.board.acts import recording, telling

if TYPE_CHECKING:
    from lem.board.acts.asked import Asked

# The longest line of why a park keeps, in characters: one line (`serve.WHY_CHARS` on `main`, a
# guess).
WHY_CHARS = 300
PARKED = "the owner parked it"


def parked(asked: Asked) -> str:
    """Park the task with his line of why, and say what happens next."""
    why = asked.given.note[:WHY_CHARS] or PARKED
    answer = partial(recording.answering, asked=asked, act="park")
    park.parked(asked.checkout, asked.slug, why, answer=answer)
    told = telling.told(
        asked.checkout, asked.slug, asked.now, "it closes once you have left it"
    )
    return f"The task is parked. {told} /lem resume {asked.slug} in any session brings it back."
