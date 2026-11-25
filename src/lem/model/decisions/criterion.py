"""A change of a criterion the owner approved, recorded in the build (`decisions.cmd_criterion`
on `main`).

N is the criterion's number in the criteria as they stand after every earlier change. `--decision`
names the decision of the record that led to it (a pick of the ladder, or the owner's help on a
breaker, which makes the change his); without one, it is the lead's own change or the personas'
clear pick. The change is checked against the criteria as they stand, so a wrong record never
enters.
"""

from types import MappingProxyType
from typing import TYPE_CHECKING, Literal

from lem.kernel.errors import Refusal
from lem.model.decisions import applied, book, ladder
from lem.records.base import Frozen
from lem.records.decisions import CriterionChanged, Taken

if TYPE_CHECKING:
    from datetime import datetime

    from lem.records.record import Record
    from lem.records.task import Task

type How = Literal["changed", "added", "removed"]

# The texts each kind of change names: before (`was`) and after (`now`).
WANTS = MappingProxyType(
    {"changed": ("was", "now"), "added": ("now",), "removed": ("was",)}
)
CODE = "criterion-form"


class Asked(Frozen, frozen=True, kw_only=True):
    """A criterion change as the command gives it."""

    how: How
    number: int
    was: str | None = None
    now: str | None = None
    why: str
    decision: int | None = None
    by: Literal["lead", "personas"] | None = None
    said: str | None = None


def sides(asked: Asked) -> None:
    """Refuse a change whose texts do not fit its kind."""
    wants = WANTS[asked.how]
    for side in ("was", "now"):
        given = bool((getattr(asked, side) or "").strip())
        if given != (side in wants):
            need = "needs" if side in wants else "takes no"
            raise Refusal(
                CODE,
                f"--{asked.how} {need} --{side}",
                "--changed N --was TEXT --now TEXT, --added N --now TEXT, or --removed N "
                "--was TEXT",
            )


def formed(asked: Asked) -> None:
    """Refuse a change whose words do not fit its kind, with no why, or that names both or
    none of a decision and who changed it."""
    sides(asked)
    if not ladder.spaced(asked.why):
        raise Refusal(CODE, "--why is empty", "give --why one plain sentence")
    if (asked.decision is None) == (asked.by is None):
        raise Refusal(
            CODE,
            "a criterion change names --decision ID or --by lead|personas, one of the two",
            "--decision names the decision of the record that led to it; --by says who "
            "changed it when none did",
        )
    if (asked.by == "personas") != (asked.said is not None):
        raise Refusal(
            CODE,
            "--said is what the personas answered, and goes with --by personas only",
            "--by personas --said WHO ANSWERED AND WHAT EACH PICKED",
        )


def known(task: Task, number: int) -> None:
    """Refuse a decision the record does not hold."""
    taken = [one.id for one in task.decisions if isinstance(one, Taken)]
    if number in taken:
        return
    listed = ", ".join(map(str, taken)) or "none"
    raise Refusal(
        "no-decision",
        f"no decision {number} in {task.slug}; its decisions: {listed}",
        f"lem decisions list {task.slug} names them",
    )


def change_of(task: Task, asked: Asked, now: datetime) -> CriterionChanged:
    """The change as the record keeps it, on the task's newest approval."""
    approvals = task.criteria.approvals
    if not approvals:
        raise Refusal(
            "not-approved",
            f"{task.slug} has no approved criteria, so no change of them is recorded",
            "its plan's criteria are their one source; lem criteria approve keeps approved "
            "criteria",
        )
    return CriterionChanged(
        id=len(task.decisions) + 1,
        at=now,
        how=asked.how,
        criterion=asked.number,
        why=ladder.spaced(asked.why),
        approval=approvals[-1].number,
        was=asked.was.strip() if asked.was else None,
        now=asked.now.strip() if asked.now else None,
        decision=asked.decision,
        by=asked.by,
        said=ladder.spaced(asked.said) if asked.said else None,
    )


def recorded(record: Record, *, asked: Asked, now: datetime) -> Record:
    """The record with the change `asked`, checked against the criteria as they stand."""
    task = record.task
    book.writable(task)
    formed(asked)
    if asked.decision is not None:
        known(task, asked.decision)
    change = change_of(task, asked, now)
    current = [
        one
        for one in task.decisions
        if isinstance(one, CriterionChanged) and one.approval == change.approval
    ]
    applied.expected_of(task.criteria.approvals[-1], (*current, change))
    return book.added(record, change, now)
