"""The feed's words of a decision's entry: the decision the task's record holds under its id, a
breaker, or a criterion's change (`decision.taken`, `decision.breaker` and `decision.criterion`
of `main`'s `SAYS`)."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.board.views.activity.told import ALERT, CHECK, DONE, USER, YOU, Told
from lem.board.views.chips import BREAKS
from lem.records.decisions import Breaker, CriterionChanged, Taken

if TYPE_CHECKING:
    from lem.records.journal.task import DecisionNoted
    from lem.records.task import Task

BY_WHOM = MappingProxyType(
    {
        "lead": "the agent",
        "personas": "the personas",
        "owner": "you",
        "lem": "Lem",
        "experts": "the experts",
        "gate": "the question gate",
        "dialectic": "the dialectic",
    }
)
IRREVERSIBLE = MappingProxyType(
    {
        "data": "it destroys or rewrites data outside the worktree",
        "system": "it writes to a system outside the repository",
        "person": "it sends something to a person",
        "money": "it spends money",
    }
)
HOW = MappingProxyType(
    {"changed": "changed", "added": "was added", "removed": "was removed"}
)


def decision(entry: DecisionNoted, task: Task) -> Told:
    """A decision's entry in the words of the decision the record holds under its id."""
    same = (one for one in task.decisions if one.id == entry.id)
    found = next(same, None)
    if isinstance(found, Taken):
        return taken(found)
    if isinstance(found, Breaker):
        return breaker(found, task.slug)
    if isinstance(found, CriterionChanged):
        how = HOW[found.how]
        return Told(YOU, ALERT, f"Criterion {found.criterion} {how}", found.why)
    return Told(DONE, CHECK, f"Decision {entry.id}", entry.what)


def taken(found: Taken) -> Told:
    """A decision taken: the owner's help on a breaker, or what a level chose."""
    if found.by == "owner" and found.breaker is not None:
        note = f"“{found.words}”" if found.words else ""
        head = f"You helped on breaker {found.breaker}"
        return Told(YOU, USER, head, found.chose, note)
    who = BY_WHOM[found.by]
    chose = f"{found.what} → {found.chose}"
    return Told(DONE, CHECK, f"Decision {found.id}, by {who}", chose)


def breaker(found: Breaker, slug: str) -> Told:
    """A breaker that stopped the build: why, and where its document is."""
    head = f"The build of {slug} stopped: {found.what}"
    sub = f"breaker {found.id} · {found.document} in the task directory"
    return Told(YOU, ALERT, head, stop_words(found), sub)


def stop_words(found: Breaker) -> str:
    """Why a breaker stopped the build: its cause, and the kind of step no "no" undoes."""
    said = BREAKS[found.cause]
    if found.cause != "irreversible" or found.irreversible is None:
        return said
    kind = IRREVERSIBLE[found.irreversible]
    return f"{said}: {kind}"
