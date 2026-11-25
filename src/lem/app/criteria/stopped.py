"""A change of the criteria that stopped between its record and its file: the record asks his
yes to the new text, and `criteria.md` still holds the text before (`kept_before` on `main`).
Running the change again with the same file ends it; until then nothing approves the file, and
nothing asks again."""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.criteria import digest, waits

if TYPE_CHECKING:
    from pathlib import Path

    from lem.app.criteria.where import Here
    from lem.records.record import Record


def unmoved(here: Here, record: Record, raw: bytes, path: Path) -> None:
    """Refuse the yes to the task's `criteria.md` while a change of it stopped between its
    record and its file: the wait that stands shows other bytes."""
    question = waits.question_of(record.task)
    shows = question.digest if question else None
    if path != here.sheet or shows is None:
        return
    if shows == digest.shown(raw):
        return
    raise Refusal(
        "changed-meanwhile",
        f"{path.name} is not the text the wait of {here.slug} shows",
        f'lem criteria change {here.slug} --file FILE --words "HIS NOTE" again with the same '
        "file ends the change; then put the criteria to him again",
    )
