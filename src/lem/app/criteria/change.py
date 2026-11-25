"""`lem criteria change --file` and `--pairs`: a change of the criteria from the owner's note,
and its pairs again (`criteria.cmd_change` and `cmd_pairs` on `main`).

The change keeps the text he answered in the record, asks his yes again under a new question,
and then writes FILE as the task's `criteria.md`; it approves nothing. Run again with the same
file, it ends a change that stopped between the two. Its pairs print each changed criterion's
text before beside its text after, which the page shows him.
"""

from functools import partial
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.criteria import stopped, texts, where
from lem.app.decisions.writing import Change, written
from lem.kernel import clock, files
from lem.kernel.errors import Refusal
from lem.model.criteria import digest, note, waits
from lem.model.decisions.words import spaced

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record

    type Made = tuple[Change, note.Shown]


def changing(here: where.Here, words: str, text: str, record: Record) -> Made:
    """The change to the criteria `text` from his note `words`, for the record as it is."""
    task = record.task
    again = note.resumed(task, digest.shown(text.encode()))
    if not again:
        raw = texts.bytes_of(here.sheet, "the criteria that wait for his yes")
        stopped.unmoved(here, record, raw, here.sheet)
        answered = texts.text_of(raw, here.sheet)
        task = note.fresh(task, (answered, text), words, clock.now())
    said = note.shown_of(task, str(here.sheet), text, again=again)
    return partial(replace, task=task), said


def changed(folder: Path, slug: str, path: Path, words: str) -> note.Shown:
    """`lem criteria change SLUG --file FILE --words NOTE`: the record first, then the file."""
    note = spaced(words)
    if not note:
        raise Refusal(
            "no-words",
            "change needs --words: his note the change comes from",
            '--words "HIS NOTE", in his words',
        )
    text = texts.text_of(texts.bytes_of(path, "the changed criteria"), path)
    here = where.here_of(folder, slug)
    with here.held():
        said = written(here.workspace.state, slug, partial(changing, here, note, text))
        files.write_whole(here.sheet, text.encode())
    return said


def again(folder: Path, slug: str) -> note.Shown:
    """`lem criteria change SLUG --pairs`: the pairs of the newest change, while its wait
    stands."""
    here = where.here_of(folder, slug)
    record = here.read()
    hold = waits.hold_of(record.task)
    if hold is None or hold.line != waits.CHANGED:
        raise Refusal(
            "no-change",
            f"no change of {slug}'s criteria waits for the owner's yes",
            f"the pairs are of a change that waits: lem criteria change {slug} --file FILE",
        )
    raw = texts.bytes_of(here.sheet, "the changed criteria")
    stopped.unmoved(here, record, raw, here.sheet)
    text = texts.text_of(raw, here.sheet)
    return note.shown_of(record.task, str(here.sheet), text, again=False)
