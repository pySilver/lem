"""His Park of a task a breaker holds, from the board (`serve.act_park` on `main`): `lem task park
SLUG --why WHY` with his one line of why, the act in the journal, and the word to its session.

The park answers the breaker's question by putting the task aside: the breaker's hold goes aside
with it, so a later answer to that question finds the task parked and says so, and his resume
gives the breaker back to answer anew (`app/tasks/park.py`).
"""

from typing import TYPE_CHECKING

from lem.app.tasks import park
from lem.board.acts import noting, telling

if TYPE_CHECKING:
    from lem.board.acts.asked import Asked
    from lem.records.questions import Question

# The longest line of why a park keeps, in characters: one line (`serve.WHY_CHARS` on `main`, a
# guess).
WHY_CHARS = 300
PARKED = "the owner parked it"


def parked(asked: Asked, question: Question) -> str:
    """Park the task with his line of why, and say what happens next."""
    why = asked.given.note[:WHY_CHARS] or PARKED
    park.parked(asked.checkout, asked.slug, why)
    entry = noting.act_of(
        "park", asked.asker, asked.now, question=question.id, option="park"
    )
    noting.noted(asked.state, asked.slug, entry)
    told = telling.told(
        asked.checkout, asked.slug, asked.now, "it closes once you have left it"
    )
    return f"The task is parked. {told} /lem resume {asked.slug} in any session brings it back."
