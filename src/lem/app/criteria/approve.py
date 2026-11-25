"""`lem criteria approve --small`: Lem approves the one criterion of a fast-track task in the
owner's name, from the task's `criteria.md`.

It is only ever the task's first contract: a task with an approval is refused. The digest is of
the size and the criteria's sentences, so an approval names the text it approved. The owner's
approval with `--file`, the lead's with `--read`, `--alone` and a request someone else wrote are
the step `criteria`'s.
"""

import hashlib
from functools import partial
from typing import TYPE_CHECKING

import msgspec
from msgspec.structs import replace

from lem.app.criteria import sheet
from lem.kernel import clock
from lem.kernel.errors import Refusal
from lem.records.approvals import Approval
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record

DIGEST = 16


def digest_of(read: sheet.Sheet) -> str:
    """One mark of the size and the criteria's sentences (`criteria.text_digest` on `main`)."""
    texts = [" ".join(criterion.text.split()) for criterion in read.criteria]
    encoded = msgspec.json.encode([read.size, texts])
    return hashlib.sha256(encoded).hexdigest()[:DIGEST]


def check(slug: str, found: Record, read: sheet.Sheet) -> None:
    """Refuse an approval in his name that is not a fast-track task's first contract."""
    if found.task.criteria.approvals:
        raise Refusal(
            "approved",
            f"{slug} has an approval already; Lem approves in his name only the first",
            "the owner approves a change of the criteria himself",
        )
    if read.size != "small" or len(read.criteria) != 1:
        raise Refusal(
            "not-small",
            f"--small approves one criterion of size small, and {sheet.NAME} has "
            f"{len(read.criteria)} of size {read.size}",
            "a task with more than one criterion takes the standard track",
        )


def with_approval(found: Record, *, approval: Approval) -> Record:
    """The record with the approval and the criteria it approved."""
    criteria = replace(
        found.task.criteria,
        size=approval.size,
        why=approval.why,
        criteria=approval.criteria,
        digest=approval.digest,
        approvals=(approval,),
    )
    return replace(found, task=replace(found.task, criteria=criteria))


def approved(folder: Path, slug: str) -> Approval:
    """Approve the one criterion of `criteria.md` in the owner's name."""
    state = places.workspace(folder).state
    found = tasks.read(state, slug)
    read = sheet.sheet_of(places.task_folder(state, slug) / sheet.NAME)
    check(slug, found, read)
    approval = Approval(
        number=1,
        at=clock.now(),
        by="lem",
        size=read.size,
        why=read.why,
        digest=digest_of(read),
        criteria=read.criteria,
    )
    tasks.update(state, slug, partial(with_approval, approval=approval), found.revision)
    return approval
