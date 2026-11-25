"""One setting written into the local, home or machine file, or taken out with `default`.

The edit goes through tomlkit, so every other line of the file stays, its comments too. It runs
under the file's lock from the read to the rename, so that two writers at one moment each keep
the other's line; the new text is read back and checked as the file's place reads it before it
replaces the file, so a wrong value is refused and the file stays as it was. A file left with
nothing but Lem's own first line goes. Nothing writes the team's file: it is everybody's, edited
by hand and committed.
"""

import tomllib
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

import tomlkit

from lem.kernel import files, locks
from lem.settings import lines, places, reading, words
from lem.settings.load import Loaded, loaded

if TYPE_CHECKING:
    from pathlib import Path

    from tomlkit.toml_document import TOMLDocument


def changed(doc: TOMLDocument, table: str, key: str, given: words.Typed | None) -> str:
    """The text with `table.key` set to `given`, or taken out with None, and a table left
    with no key and no comment of the owner's taken out too."""
    held = doc.get(table)
    if given is None and held is not None:
        held.pop(key, None)
        if not held and not commented(held):
            doc.pop(table)
    elif given is not None:
        doc.setdefault(table, tomlkit.table())[key] = given
    return tomlkit.dumps(doc)


def commented(held: object) -> bool:
    """Whether a table holds a comment, on its header's line or a line of its own."""
    trivia = getattr(held, "trivia", None)
    on_header = bool(getattr(trivia, "comment", ""))
    as_string = getattr(held, "as_string", str)
    return on_header or "#" in as_string()


@dataclass(frozen=True, kw_only=True, slots=True)
class Edit:
    """One setting to write: the file's place, its path and its lock, the table, the key, and
    the value, None to take the line out."""

    scope: places.Scope
    path: Path
    lock: Path
    table: str
    key: str
    given: words.Typed | None


def written(edit: Edit, where: reading.Where) -> Loaded:
    """Write `edit` into its file, and give the settings then in force. The settings are
    loaded whole with the file as the edit leaves it before anything is written: a refusal of
    any file leaves this one byte for byte as it was."""
    text = lines.text_of(edit.path)
    new = edited_text(text, edit)
    found = loaded_with(where, edit.scope, new)
    if lines.only_lems(new, edit.scope):
        edit.path.unlink(missing_ok=True)
    elif new != text:
        files.write_whole(edit.path, new.encode("utf-8"))
    return found


def edited_text(text: str, edit: Edit) -> str:
    """The text of the file as `edit` leaves it."""
    doc = lines.document(text, edit.scope)
    return changed(doc, edit.table, edit.key, edit.given)


def loaded_with(where: reading.Where, scope: places.Scope, new: str) -> Loaded:
    """The settings in force with the file of `scope` read as the text `new`, every file
    checked."""
    edited = ((scope, tomllib.loads(new)),)
    return loaded(replace(where, edited=edited))


def applied(edit: Edit, where: reading.Where) -> Loaded:
    """`written` under the file's lock, from the read to the rename."""
    with locks.held(edit.lock):
        return written(edit, where)
