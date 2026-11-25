"""What a breaker needs before it trips: its document in the task's folder, the handoff beside
it, and the work committed (`decisions.cmd_breaker` on `main`)."""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.decisions import breaker

if TYPE_CHECKING:
    from lem.app.criteria.where import Here
    from lem.app.wiring import Ports
    from lem.records.record import Record

DOCUMENT = "breaker.md"
FORM = "in the form of templates/breaker.md"


@dataclass(frozen=True, kw_only=True, slots=True)
class Asked:
    """A breaker as the command asks it: its cause, the kind of an irreversible step, and the
    document's path (None: `breaker.md` of the task's folder)."""

    cause: breaker.Cause
    kind: breaker.Kind | None = None
    document: str | None = None


def document_of(here: Here, named: str | None) -> Path:
    """The breaker's document: `named`, else `breaker.md` of the task's folder; refused when it
    is not a file of that folder, where the board and a fresh agent read it."""
    path = Path(named) if named else here.folder / DOCUMENT
    path = path if path.is_absolute() else Path.cwd() / path
    if not path.is_file():
        raise Refusal(
            "no-document",
            f"{path} is not a file",
            f"write the breaker's document first, {DOCUMENT} in the task's folder, {FORM}",
        )
    if path.resolve().parent != here.folder.resolve():
        raise Refusal(
            "document-place",
            f"{path} is not in the task's folder {here.folder}",
            "write it there: the board and a fresh agent read the breaker's document there",
        )
    return path


def ready(ports: Ports, here: Here) -> None:
    """Refuse a breaker with no handoff beside its document, or with work not committed: a
    dropped task's worktree goes, and only its branch stays."""
    handoff = here.folder / breaker.HANDOFF
    if not handoff.is_file() or not handoff.read_text(encoding="utf-8").strip():
        raise Refusal(
            "no-handoff",
            f"{handoff} is missing",
            "write the handoff beside the document (what is settled, what is open, the next "
            "step, what was tried and failed), so a fresh agent goes on from it",
        )
    worktree = here.worktree
    if (worktree / ".git").exists() and not ports.git.clean(worktree):
        raise Refusal(
            "not-committed",
            f"the worktree {worktree} has changes that no commit holds",
            "commit what the task has first: a dropped task's worktree goes, and only its "
            "branch stays",
        )


def checked(ports: Ports, here: Here, record: Record, asked: Asked) -> Path:
    """The breaker's document, after every check of the breaker `asked`."""
    breaker.why_of(asked.cause, asked.kind)
    breaker.trippable(record.task)
    path = document_of(here, asked.document)
    ready(ports, here)
    return path
