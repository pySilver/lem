"""Which of a task's decisions are important, and so wait for a look (`board_model.importance`
on `main`): a reason of the newest proposal names it (it makes the pull request not green), it
went past the personas (the dialectic or the experts took it or answered at their level), no
level of the ladder settled it, or it is the owner's help on a breaker. A breaker is none: it
stands on its own row."""

from typing import TYPE_CHECKING

from lem.records.decisions import Taken

if TYPE_CHECKING:
    from lem.records.record import Record

PAST_PERSONAS = frozenset(("dialectic", "experts"))


def important(record: Record) -> tuple[Taken, ...]:
    """The task's important decisions, in their order."""
    landing = record.landing
    proposed = landing.proposed if landing else None
    reasons = proposed.reasons if proposed else ()
    taken = (one for one in record.task.decisions if isinstance(one, Taken))
    return tuple(one for one in taken if weighs(one, reasons))


def weighs(decision: Taken, reasons: tuple[str, ...]) -> bool:
    """Whether the decision is important, by the proposal's `reasons`."""
    named = any(line.startswith(f"decision {decision.id} ") for line in reasons)
    return named or past(decision) or decision.unsettled or helped(decision)


def past(decision: Taken) -> bool:
    """Whether it went past the personas."""
    answered = any(
        level in PAST_PERSONAS and said.strip() for level, said in decision.levels
    )
    return decision.by in PAST_PERSONAS or answered


def helped(decision: Taken) -> bool:
    """Whether it is the owner's help on a breaker."""
    return decision.by == "owner" and decision.breaker is not None
