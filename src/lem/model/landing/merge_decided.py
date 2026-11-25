"""The task's decisions in the body of the one commit a squash makes, one line each, so that the
base's history keeps them after the prune folds the task's record (amendment A2 of the rebuild's
roadmap, 2026-11-25).

A decision taken by a level of the ladder names what was asked, what was chosen, who chose it and
why; a criterion's change names the criterion and both texts; a stop at the circuit breaker names
what stopped. A task with no decision adds no lines.
"""

from typing import TYPE_CHECKING

from lem.model.landing.green_words import reason, taken_by
from lem.records.decisions import Breaker, CriterionChanged, Taken

if TYPE_CHECKING:
    from lem.records.decisions import Decision

HEADING = "Decisions of the task:"


def texts_of(change: CriterionChanged) -> str:
    """The criterion's texts a change names: the one it had and the one it has, or the one
    it added or removed."""
    was = reason(change.was or "")
    now = reason(change.now or "")
    if change.how == "changed":
        return f'"{was}" is now "{now}"'
    if change.how == "added":
        return f'"{now}"'
    return f'"{was}"'


def changed(change: CriterionChanged) -> str:
    """One criterion's change, with its texts, and why."""
    named = f"criterion {change.criterion} {change.how}"
    return f"- {named}: {texts_of(change)}. {reason(change.why)}."


def line(decision: Decision) -> str:
    """One decision of the record as a line of the commit's body."""
    if isinstance(decision, Taken):
        why = reason(decision.why)
        return f'- {decision.what}: "{decision.chose}", by {taken_by(decision)}. {why}.'
    if isinstance(decision, Breaker):
        return f"- the build stopped at breaker {decision.id}: {reason(decision.what)}."
    return changed(decision)


def block(decisions: tuple[Decision, ...]) -> str | None:
    """The part of the commit's body that lists the decisions, or None when there are none."""
    if not decisions:
        return None
    return "\n".join((HEADING, *map(line, decisions)))
