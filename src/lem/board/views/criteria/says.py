"""What a decision's row says (`board_model.importance`, `decision_says` and `chosen_at` on
`main`): why it is important, how and why it was taken and by whom, each level of the ladder it
climbed, and which of its options it took.

A decision is important when a reason of the newest proposal names it (it makes the pull request
not green), when it went past the personas, when no level of the ladder settled it, or when it
is the owner's help on a breaker.
"""

import re
from typing import TYPE_CHECKING

from lem.board.views.criteria.terms import BY_WHOM, EXPERTS, LADDER, PAST_PERSONAS
from lem.board.views.words import capital

if TYPE_CHECKING:
    from lem.records.decisions import Taken
    from lem.records.record import Record

# The short label before a colon that a lead writes for an option (`B: a line of its own`).
OPTION_LABEL = re.compile(r"^([A-Za-z0-9]{1,3}):\s")


def past_of(taken: Taken) -> str | None:
    """How the decision went past the personas: taken, or answered, by a level above them."""
    if taken.by in PAST_PERSONAS:
        who = BY_WHOM[taken.by]
        return f"it went past the personas: {who} took it"
    said = dict(taken.levels)
    answered = [one for one in PAST_PERSONAS if said.get(one, "").strip()]
    if not answered:
        return None
    who = BY_WHOM[answered[0]]
    return f"it went past the personas: {who} answered it"


def importance(record: Record, taken: Taken) -> str | None:
    """Why the decision is important, or None."""
    proposed = record.landing.proposed if record.landing else None
    reasons = proposed.reasons if proposed else ()
    named = any(line.startswith(f"decision {taken.id} ") for line in reasons)
    helped = taken.by == "owner" and taken.breaker is not None
    parts = (
        "it makes the pull request not green" if named else None,
        past_of(taken),
        "no level of the ladder settled it: the agent’s pick stands"
        if taken.unsettled
        else None,
        f"it is your help on breaker {taken.breaker}" if helped else None,
    )
    return ", and ".join(part for part in parts if part) or None


def how_who(taken: Taken) -> tuple[str, str]:
    """How the decision was taken and why, and by whom, in a few words."""
    if taken.by == "owner" and taken.breaker is not None:
        words = f": “{taken.words}”" if taken.words else ""
        how = f"your help on breaker {taken.breaker}{words}, because {taken.why}"
        return how, f"by you, on breaker {taken.breaker}"
    if taken.unsettled:
        how = f"the agent’s pick, which no level of the ladder settled, because {taken.why}"
        return how, "the agent’s pick, which no level settled"
    who = BY_WHOM.get(taken.by, taken.by)
    picked = ""
    if taken.by == "experts":
        count = len(taken.advisers or EXPERTS)
        picked = (
            ", as the one expert picked it" if count == 1 else ", as both picked it"
        )
    return f"taken by {who}{picked}, because {taken.why}", f"by {who}"


def levels(taken: Taken) -> tuple[str, ...]:
    """Each level of the ladder the decision climbed, in the ladder's order, then any other."""
    said = dict(taken.levels)
    named = dict(LADDER)
    keys = [key for key in named if key in said]
    keys += [key for key in said if key not in named]
    return tuple(level_line(key, said[key]) for key in keys)


def level_line(key: str, said: str) -> str:
    """One level of the ladder: its name in bold (its key, for a level the ladder does not
    know), and what it said."""
    shown = dict(LADDER).get(key) or capital(key)
    return f"**{shown}:** {said}"


def chosen_at(taken: Taken) -> int:
    """The option the decision took, by its place in its options, or -1: the same text, or
    the same short label before a colon when one option alone has it."""
    if taken.chose in taken.options:
        return taken.options.index(taken.chose)
    wanted = label_of(taken.chose)
    labels = list(map(label_of, taken.options))
    if wanted is None or labels.count(wanted) != 1:
        return -1
    return labels.index(wanted)


def label_of(option: str) -> str | None:
    """The short label before an option's colon, or None."""
    found = OPTION_LABEL.match(option)
    return found[1] if found else None
