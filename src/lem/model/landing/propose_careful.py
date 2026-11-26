"""Why a request is careful, and whether its plan called for a plan talk
(`main:land.careful`, `settings_edit`, `local_settings_edit`, `talk_due`).

The shape's topics, the plan's own call and the newest review's call are judgments against the
project's topics; an edit of Lem's own settings, or a commit of one machine's, is the one rule
matched here by itself: the file says for every later task what is careful, what the checks
run, who merges and where a task lands (audit A1 and N5 of 2026-11-17 on `main`).
"""

from typing import TYPE_CHECKING

from lem.model.landing import careful, careful_words
from lem.model.landing.green_words import reason
from lem.model.landing.review import newest
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.model.landing.propose_facts import Facts
    from lem.records.record import Record

# Only the presence of the local settings matters.
PRESENT = ""


def edits(facts: Facts) -> tuple[str, ...]:
    """The reasons of the change's edits of Lem's own settings."""
    found = facts.settings
    team = careful.Seen(
        touched=careful.SETTINGS_FILE in facts.changed,
        base=found.before,
        tip=found.after,
    )
    was, now = found.local
    local = careful.Seen(
        touched=careful.LOCAL_SETTINGS_FILE in facts.changed,
        base=PRESENT if was or not now else None,
        tip=PRESENT if now or not was else None,
    )
    return careful.settings_reasons(careful.Edits(settings=team, local=local))


def why(record: Record, facts: Facts) -> tuple[str, ...]:
    """Each reason the request is careful; none when it is not: the shape's topics, the
    owner's word, the plan's call, an edit of Lem's settings, and the newest review's call."""
    task = record.task
    topics = task.shape.careful if task.shape else ()
    plan = ("the plan says so",) if task.plan and task.plan.careful else ()
    return (
        careful_words.owner_says(record)
        + topics
        + plan
        + edits(facts)
        + review_call(record)
    )


def review_call(record: Record) -> tuple[str, ...]:
    """The newest answered review's careful call, with its reason, when it said yes."""
    last = newest(record.landing or Landing())
    if last is None or not last.careful:
        return ()
    said = reason(last.careful_why or "no reason given")
    return (f"the review says so: {said}",)
