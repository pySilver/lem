"""The approval of the criteria and each change of an approved criterion during the build, on
the card of the criteria (`board_task.criteria_head` and `board_model.taken_over` on `main`). A
change the owner approved afterwards is his, and no cause of not green."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.board.inputs.clock import stamp
from lem.board.inputs.parts import Row
from lem.board.views.criteria.heads import APPROVED
from lem.board.views.criteria.terms import BY_WHOM
from lem.model.decisions.changes import changes_of

if TYPE_CHECKING:
    from lem.board.views.world import Seen, World
    from lem.model.decisions.changes import Past
    from lem.records.approvals import Approval
    from lem.records.decisions import CriterionChanged

STANDARD = (
    "You may still say “/lem standard-track”: then the personas read it, and your "
    "approval replaces this one."
)
FROZEN = (
    "The whole request was written, and nobody was confused: the build started, and you "
    "can still stop it or change a criterion."
)
ICONS = MappingProxyType({"owner": "check", "read": "users"})
HOW = MappingProxyType(
    {"changed": "changed", "added": "was added", "removed": "was removed"}
)
SAID = MappingProxyType({"lem": STANDARD, "read": FROZEN})


def subs_of(approval: Approval) -> tuple[str, ...]:
    """The lines under the approval: what the fast track and a frozen read still allow, and
    its number with the one it replaces."""
    said = SAID.get(approval.by)
    lines = [said] if said else []
    replaces = approval.replaces
    if approval.number > 1 or replaces is not None:
        tail = "" if replaces is None else f"; it replaces approval {replaces}"
        lines.append(f"approval {approval.number}{tail}")
    return tuple(lines)


def approval_row(world: World, seen: Seen) -> Row | None:
    """The newest approval: who gave it, and whether the personas' read was in before it."""
    criteria = seen.record.task.criteria
    if not criteria.approvals:
        return None
    approval = criteria.approvals[-1]
    read = criteria.reads[-1] if criteria.reads else None
    after = ""
    if read is not None and approval.by == "owner":
        before = read.started < approval.at
        after = (
            "after the personas’ read" if before else "before the personas’ read was in"
        )
    return Row(
        id="crit-approved",
        look="done" if approval.by == "owner" else "quiet",
        icon=ICONS.get(approval.by, "user"),
        head=APPROVED[approval.by],
        text=after or None,
        subs=subs_of(approval),
        time=stamp(approval.at, world.clock.now, world.clock.zone),
    )


def change_row(world: World, past: Past) -> Row:
    """A change of an approved criterion during the build, and whether the owner took it
    over."""
    change, his = past.change, past.taken_over_by
    yours = his is not None
    how = HOW[change.how]
    said = {
        "changed": f"was “{change.was}”, now “{change.now}”",
        "added": f"“{change.now}”",
        "removed": f"was “{change.was}”",
    }
    return Row(
        id=f"crit-change-{change.id}",
        look="done" if yours else "you",
        icon="check" if yours else "triangle-exclamation",
        head=f"Criterion {change.criterion} {how} during the build",
        subs=(said[change.how], why_of(change, his)),
        time=stamp(change.at, world.clock.now, world.clock.zone),
    )


def why_of(change: CriterionChanged, his: int | None) -> str:
    """Why the criterion changed, who changed it, and whether the change is his now."""
    who, took = who_of(change), took_of(his)
    return f"{change.why} · {who} · {took}"


def who_of(change: CriterionChanged) -> str:
    """Who changed the criterion: a decision, or the agent or the personas with their
    words."""
    if change.decision is not None:
        return f"after decision {change.decision}"
    by = BY_WHOM[change.by or "lead"]
    return f"by {by}: {change.said}" if change.said else f"by {by}"


def took_of(his: int | None) -> str:
    """Whether the owner's approval made the change his."""
    if his is None:
        return "the pull request is not green for it"
    return (
        f"Approved by you afterwards (approval {his}): it is yours, and no cause of not "
        "green"
    )


def change_rows(world: World, seen: Seen) -> tuple[Row, ...]:
    """Each change of an approved criterion, in order."""
    history = changes_of(seen.record.task).history
    return tuple(change_row(world, past) for past in history)
