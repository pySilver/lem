"""The server's notes and duties as a page and its stream read them."""

from typing import TYPE_CHECKING

from lem.board.acts.notes import NOTES
from lem.board.duties.memory import MEMORY
from lem.board.inputs.parts import Note

if TYPE_CHECKING:
    from pathlib import Path


def revision(state: Path) -> str:
    """The current workspace's merge notes and the duty results that appear on its pages."""
    checkout = state.parent.parent
    kept = MEMORY.of(checkout)
    notes = snapshot(str(checkout))
    shown = (
        notes,
        tuple(kept.problems.values()),
        sorted(kept.running()),
        kept.said.copy(),
    )
    return repr(shown) if any(shown) else ""


def note_of(token: str | None, checkout: Path, slug: str | None) -> Note | None:
    """The outcome of the act, or the server's last word on the open task's merge."""
    note = NOTES.get(token)
    if note is None:
        said = MEMORY.of(checkout).said.get(slug or "")
        return Note(look="lem", icon="code-pull-request", said=said) if said else None
    if note.state == "done":
        return Note(look="ok", icon="check", word="Done.", said=note.said)
    if note.state == "running":
        return Note(look="lem", icon="clock", word="Running.", said=note.said)
    if note.state == "stands":
        return Note(look="you", icon="clock", said=note.said)
    return Note(look="bad", icon="alert", word="Not done.", said=note.said)


def snapshot(checkout: str) -> tuple[tuple[str, str, object], ...]:
    """The running tokens and notes of one workspace, read under their shared lock."""
    with NOTES.lock:
        return tuple(
            (slug, token, NOTES.kept.get(token))
            for (folder, slug), token in NOTES.merging.items()
            if folder == checkout
        )
