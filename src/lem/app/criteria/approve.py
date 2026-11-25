"""`lem criteria approve`: keep the criteria that were approved, word for word, with their mark
and a number of their own (`criteria.cmd_approve` on `main`).

The owner's yes approves FILE as it is, or, with `--shown`, the bytes his page showed and nothing
else. `--small` is Lem's approval of a fast-track task's one criterion in his name, from the
task's `criteria.md`; `--read` the lead's freeze of the plan's criteria after a clear read;
`--alone` an approval while the task runs without him, a night's task or while he is away.
"""

from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING

from lem.app.criteria import mode, show, stopped, texts, where
from lem.app.decisions.writing import Change, written
from lem.kernel import clock
from lem.kernel.errors import Refusal
from lem.model.criteria import approve, digest
from lem.model.criteria.read import sheet_of

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.approvals import Approval, ApprovedBy
    from lem.records.record import Record

THE_CRITERIA = "the criteria approved"


@dataclass(frozen=True, kw_only=True, slots=True)
class Asked:
    """An approval as the command asks it: by whom, the file (None: the task's own), and the
    mark of the bytes his page showed."""

    by: ApprovedBy
    path: Path | None = None
    shown: str | None = None


def unchanged_since(path: Path, raw: bytes, shown: str | None) -> None:
    """Refuse a file whose bytes are not the ones his page showed."""
    if shown is None or digest.shown(raw) == shown:
        return
    raise Refusal(
        "shown-changed",
        f"{path.name} changed since the page showed it (the page showed {shown}): nothing "
        "was approved",
        "read the criteria again, then approve",
    )


def make(
    here: where.Here, asked: Asked, path: Path, record: Record
) -> tuple[Change, Approval]:
    """The approval of the file `path` for the record as it is, and what it approves."""
    raw = texts.bytes_of(path, THE_CRITERIA)
    unchanged_since(path, raw, asked.shown)
    stopped.unmoved(here, record, raw, path)
    approving = approve.Asked(
        by=asked.by,
        sheet=sheet_of(texts.text_of(raw, path), path.name),
        alone=mode.alone(record),
        other=mode.not_his(record),
        plan=asked.by in {"read", "alone"},
    )
    now = clock.now()
    change = partial(approve.approved, asked=approving, now=now)
    return change, approve.approval_of(record.task, approving, now)


def approved(folder: Path, slug: str, asked: Asked) -> Approval:
    """Approve the criteria of `asked` for the task `slug`."""
    here = where.here_of(folder, slug)
    path = asked.path
    if asked.by == "read":
        path, _ = show.source(here, here.read())
    elif path is None:
        path = here.sheet
    return written(here.workspace.state, slug, partial(make, here, asked, path))
