"""The words green and the pull request's text share for the record's decisions: who took one,
whether it was the owner's and taken without him, and why a criterion changed
(`main:land.taken_by`, `without_him`, `owners_change`, `change_why`)."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.records.decisions import CriterionChanged, Taken

if TYPE_CHECKING:
    from collections.abc import Mapping

    from lem.records.decisions import Level
    from lem.records.record import Record

# Who took a decision of the record, as the text of a pull request names them.
TAKEN_BY: Mapping[Level, str] = MappingProxyType(
    {
        "lead": "the lead",
        "gate": "the gate",
        "personas": "the personas",
        "dialectic": "the dialectic",
        "owner": "the owner",
        "lem": "Lem",
        "experts": "the experts",
    }
)
# The levels of the ladder whose decision, taken without the owner, is never green: past
# the personas.
PAST_PERSONAS = frozenset(("dialectic", "experts"))


def reason(text: str) -> str:
    """A reason as written, without its own full stop, for a sentence around it."""
    return text.rstrip(".")


def taken_by(decision: Taken) -> str:
    """Who took a decision, for a line of the pull request: one expert alone is named as
    one."""
    if decision.by == "experts" and len(decision.advisers) == 1:
        return "one expert"
    return TAKEN_BY[decision.by]


def without_him(decision: Taken) -> bool:
    """Whether a decision is the owner's and was taken without him: past the personas, or a
    pick that no level of the ladder settled. He reads each one in the pull request."""
    return decision.by in PAST_PERSONAS or decision.unsettled


def led(record: Record, change: CriterionChanged) -> Taken | None:
    """The decision that led to a criterion's change, when one did."""
    return next(
        (
            decision
            for decision in record.task.decisions
            if isinstance(decision, Taken) and decision.id == change.decision
        ),
        None,
    )


def owners_change(record: Record, change: CriterionChanged) -> bool:
    """Whether a criterion's change came from the owner's own help on a breaker: his
    decision makes it his, as a later approval of his does."""
    found = led(record, change)
    return found is not None and found.by == "owner" and found.breaker is not None


def change_why(record: Record, change: CriterionChanged) -> str:
    """Why a criterion changed: the reason on record, and the decision that led to it."""
    found = led(record, change)
    if found is None:
        return change.why
    if owners_change(record, change):
        how = f"the owner's help on breaker {found.breaker}, which took"
    else:
        how = f"where {taken_by(found)} took"
    after = f"after decision {found.id} ({found.what})"
    return f'{reason(change.why)}, {after}, {how} "{found.chose}"'


def taken_over(record: Record, change: CriterionChanged) -> int | None:
    """The number of the owner's approval that took a criterion's change over, made after
    the approval the change was made on; None when none did."""
    return next(
        (
            approval.number
            for approval in record.task.criteria.approvals
            if approval.by == "owner" and approval.number > change.approval
        ),
        None,
    )
