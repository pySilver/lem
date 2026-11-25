"""Who may approve a task's criteria, and when (`criteria.approve_held` on `main`).

The owner's own yes is always allowed and always makes a new number, but not while his No to
the wait that stands is on record. Lem's approval in his name (the fast track) and the lead's
after a clear read (the standard track from a complete request) are only a task's first
contract. An approval without him (`alone`) is for a task that runs without him: a night's task,
or any task while he is away; it is never his yes.
"""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.criteria import waits

if TYPE_CHECKING:
    from lem.model.criteria.read import Sheet
    from lem.records.approvals import Approval
    from lem.records.task import Task

APPROVED = "approved"
CHANGES = "a criterion changes through its record: lem decisions criterion SLUG ..."


def no_on_record(task: Task, *, owner: bool) -> Refusal | None:
    """His No to the wait that stands refuses his yes and an approval without him: the first
    answer counts, and the No changes the criteria first."""
    said = waits.said_no(task)
    if said is None:
        return None
    note = f", with the words {said.note!r}" if said.note else ""
    then = "his yes to that text approves it" if owner else "--alone approves that text"
    return Refusal(
        "said-no",
        f"the owner said No to the criteria of this wait ({said.source}, at {said.at}"
        f"{note}), and the first answer counts: nothing was approved",
        f'lem criteria change {task.slug} --file FILE --words "HIS NOTE" writes the changed '
        f"text and a new wait, or lem criteria change {task.slug} --unchanged a new wait "
        f"of the same text; then {then}",
    )


def first_contract(task: Task, by: str) -> Refusal | None:
    """An automatic approval, Lem's or a read's, is only the task's first contract."""
    approvals = task.criteria.approvals
    if not approvals:
        return None
    kept = approvals[-1]
    return Refusal(
        APPROVED,
        f"{task.slug} has approval {kept.number} of its criteria already (by {kept.by}): "
        f"an approval by {by} is only the first contract",
        f"{CHANGES}; the track changes only by the owner's own approval, lem criteria "
        f"approve {task.slug} --file FILE",
    )


def waits_for_him(task: Task, other: str) -> Refusal:
    """A fast-track request that is not his own sentence waits for his yes while the task runs
    with him."""
    return Refusal(
        "not-his",
        f"{task.slug} is not the owner's own request ({other}), so its criterion waits for "
        "the owner's yes while the task runs with him",
        f"show it to him before its builder starts; on his yes, lem criteria approve "
        f"{task.slug} --file FILE keeps it as his",
    )


def by_lem(
    task: Task, sheet: Sheet, other: str | None, *, alone: bool
) -> Refusal | None:
    """Lem approves the fast track's one criterion in his name only when the request is his
    own sentence, in either mode."""
    if sheet.size != "small":
        return Refusal(
            "not-small",
            f"--small approves the one criterion of a fast-track task, and these criteria "
            f"say Size: {sheet.size}",
            "the standard track waits for the owner's own yes",
        )
    if other is None:
        return first_contract(task, "lem")
    if not alone:
        return waits_for_him(task, other)
    return Refusal(
        "not-his",
        f"{task.slug} is not the owner's own request ({other}), so Lem does not approve its "
        "criterion in his name",
        f"lem criteria approve {task.slug} --file FILE --alone approves it without him "
        "while the task runs without him, and its pull request is not green for it",
    )


def grew(kept: Approval, sheet: Sheet) -> bool:
    """Whether a fast-track task approved without him grew into a full change, which needs that
    track's approval."""
    return kept.by == "alone" and kept.size == "small" and sheet.size == "full"


def by_alone(
    task: Task, sheet: Sheet, other: str | None, *, alone: bool
) -> Refusal | None:
    """An approval without him: only while the task runs without him, never over his own
    approval or a read's, and for a fast track only of a request that is not his."""
    if sheet.size == "small" and other is None:
        return Refusal(
            "his-request",
            "the criteria say Size: small, and the request is the owner's own",
            f"lem criteria approve {task.slug} --small approves it in his name, in either "
            "mode",
        )
    if not alone:
        return (
            waits_for_him(task, other)
            if other
            else Refusal(
                "with-owner",
                f"{task.slug} runs with the owner: his yes approves its criteria",
                "--alone is for a task that runs without the owner",
            )
        )
    approvals = task.criteria.approvals
    kept = approvals[-1] if approvals else None
    if kept is None or kept.by == "lem" or grew(kept, sheet):
        return None
    return Refusal(
        APPROVED,
        f"{task.slug} has approval {kept.number} of its criteria already (by {kept.by})",
        CHANGES,
    )
