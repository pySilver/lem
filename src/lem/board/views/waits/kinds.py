"""How each row of what waits for the owner looks (`board_model.wait_say` on `main`): its look,
its icon, and what its time counts from; and its id, which names the question it asks."""

from types import MappingProxyType
from typing import TYPE_CHECKING, NamedTuple

from lem.app.sessions.acts import Open
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.board.inputs.text import Look
    from lem.board.views.world import Seen
    from lem.model.owner.looks import Row

ALERT = "triangle-exclamation"
PAGE = "file-lines"
IN_STATE = "in this state"
PROPOSED = "since it was proposed"
YOU: Look = "you"
BAD: Look = "bad"


class Said(NamedTuple):
    """A row's look, its icon, and the hover of its time."""

    look: Look
    icon: str
    note: str


YOURS = MappingProxyType(
    {
        "breaker": Said(YOU, ALERT, "since the build stopped"),
        "criteria": Said(YOU, PAGE, IN_STATE),
        "held": Said(YOU, "user", IN_STATE),
        "plan": Said(YOU, PAGE, IN_STATE),
        "card": Said(YOU, "user", "since the session asked"),
        "review": Said(YOU, PAGE, "since the merge agent wrote it"),
    }
)
# The topic of the question each row asks, whose id names the row.
TOPICS = MappingProxyType(
    {"breaker": "breaker", "criteria": "criterion", "plan": "plan"}
)


def said(seen: Seen, row: Row) -> Said:
    """The look, icon and time's hover of `row` of the task of `seen`."""
    found = YOURS.get(row.kind)
    if found is not None:
        return found
    if row.kind in {"session", "stopped"}:
        return Said(BAD, ALERT, session_note(seen, row))
    if row.kind == "blocked":
        note = "since Lem stopped it" if row.say else "since it stopped"
        return Said(BAD, ALERT, note)
    if row.kind == "after_dropped":
        after = " and ".join(row.after)
        verb = "were" if len(row.after) > 1 else "was"
        return Said(YOU, "user", f"since {after} {verb} dropped")
    return merge_said(seen, row)


def session_note(seen: Seen, row: Row) -> str:
    """What the time of a row of the task's session counts from."""
    status = seen.record.task.status
    if row.kind == "stopped":
        return "since Lem logged the stop"
    if row.deaf:
        return "since its session opened"
    if status == "dropped":
        return "since it was dropped"
    if status == "landed":
        return "since it was merged"
    opened = any(isinstance(act, Open) for act in seen.acts)
    return "since its last session opened" if opened else "since it opened"


def merge_said(seen: Seen, row: Row) -> Said:
    """The merge: the owner's, or a refusal or a conflict, which are faults."""
    landing = seen.record.landing or Landing()
    proposed, refused = landing.proposed, landing.refused
    turned_down = (
        refused is not None and proposed is not None and refused.tip == proposed.tip
    )
    if row.conflict or turned_down:
        return Said(BAD, ALERT, PROPOSED)
    return Said(YOU, "code-branch", PROPOSED)


def key_of(seen: Seen, row: Row) -> str:
    """The row's id on the page: the open question it asks, else its key, with `-` for `:`."""
    if row.kind == "card" and row.card:
        return row.card.replace(":", "-")
    topic = TOPICS.get(row.kind)
    task = seen.record.task
    asked = (
        one.id
        for one in reversed(task.questions)
        if one.topic == topic and one.answer is None
    )
    return next(asked, row.key).replace(":", "-")


def card_tab(row: Row) -> str | None:
    """The tab of a card's own page (`card/PAGE`, the agterm page in the card's id), or None
    for a row that is no card."""
    if row.kind != "card" or not row.card:
        return None
    page = row.card.rpartition(":")[2]
    return f"card/{page}"
