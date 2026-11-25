"""What `propose` writes and gives: the record with the proposal, the pull request and the
phase `open`, and the outcome an agent and the owner read (the pull request's number and
address, and green or each reason it is not)."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.landing import changes
from lem.records.base import Frozen
from lem.records.journal.landing import NotGreen
from lem.records.landing.record import Pull

if TYPE_CHECKING:
    from lem.records.landing.propose import MergeRead, Proposed
    from lem.records.record import Record


class Made(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """What `propose` gives: the pull request's number and address, green or each reason it
    is not, whether it is careful, who merges it, the tip and the branch, and the text's
    path in the task's folder."""

    task: str
    pull: Pull
    green: bool
    reasons: tuple[str, ...]
    careful: bool
    who_acts: str
    tip: str
    branch: str
    text: str


def opened(
    record: Record, *, made: Proposed, pull: Pull, read: MergeRead | None = None
) -> Record:
    """The record with the proposal, the pull request and the phase `open`; a request that
    is not green names its reasons in the journal."""
    changed = changes.landing(
        record, proposed=made, pull=pull, phase="open", refused=None
    )
    changed = carried(changed, made, read)
    if made.reasons:
        entry = NotGreen(at=made.at, tip=made.tip, reasons=made.reasons)
        changed = changes.noted(changed, entry)
    return changes.moved(changed, "open", f"pull request {pull.url}", made.at)


def carried(record: Record, made: Proposed, read: MergeRead | None) -> Record:
    """Save the carried read and move any approval that still stands to the new tip."""
    landing = record.landing
    if landing is None:
        return record
    if read is not None:
        record = changes.landing(record, reads=(*landing.reads, read))
    approval = made.owner_merge
    if landing.standing is None or approval is None:
        return record
    kept = (
        replace(landing.standing, tip=made.tip) if approval.state == "stands" else None
    )
    return changes.landing(record, standing=kept)


def given(record: Record, made: Proposed, where: tuple[Pull, str]) -> Made:
    """The outcome of the proposal: the pull request and the branch it is on."""
    pull, branch = where
    return Made(
        task=record.task.slug,
        pull=pull,
        green=made.green,
        reasons=made.reasons,
        careful=made.careful,
        who_acts=made.who_acts,
        tip=made.tip,
        branch=branch,
        text=made.text or "",
    )


def said(made: Made) -> str:
    """The line for the owner: the pull request's address, and green or each reason."""
    address = made.pull.url
    if made.green:
        return f"pull request {address}: green"
    listed = "; ".join(made.reasons)
    return f"pull request {address}: not green: {listed}"
