"""A change of a criterion during the build, as one line of the pull request's text
(`main:land.change_line`): what it was and is, why and the decision that led to it, who, and
the approval of the owner's that took it over."""

from typing import TYPE_CHECKING

from lem.model.landing.green_words import change_why, reason, taken_over

if TYPE_CHECKING:
    from lem.records.decisions import CriterionChanged
    from lem.records.record import Record


def flat(text: str | None) -> str:
    """A criterion's text in one line: a criterion with a case is its sentence and its
    steps, one to a line."""
    return " ".join((text or "").split())


def said_of(change: CriterionChanged) -> str:
    """What a change did: what the criterion was and is."""
    was, now = flat(change.was), flat(change.now)
    if change.how == "added":
        return f'added, "{now}"'
    if change.how == "removed":
        return f'removed, was "{was}"'
    return f'was "{was}", now "{now}"'


def who_of(record: Record, change: CriterionChanged) -> str:
    """Who changed the criterion when no decision did, and the approval of his that took
    the change over."""
    who = ""
    if change.decision is None:
        who = (
            " By the lead."
            if change.by == "lead"
            else f" By the personas: {change.said}"
        )
    later = taken_over(record, change)
    return (
        f"{who} Approved by the owner afterwards (approval {later})." if later else who
    )


def change_line(record: Record, change: CriterionChanged) -> str:
    """One change of a criterion: what it was and is, why, who, and the approval of his
    that took it over."""
    said, who = said_of(change), who_of(record, change)
    why = reason(change_why(record, change))
    return f"- criterion {change.criterion}: {said}. {why}.{who}"
