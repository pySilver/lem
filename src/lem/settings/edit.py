"""One setting written into the local, home or machine file, or taken out with `default`.

The edit goes through tomlkit, so every other line of the file stays, its comments too. It runs
under the file's lock from the read to the rename, so that two writers at one moment each keep
the other's line; the new text is read back and checked as the file's place reads it before it
replaces the file, so a wrong value is refused and the file stays as it was. A file left with
nothing but Lem's own first line goes. Nothing writes the team's file: it is everybody's, edited
by hand and committed.
"""

import tomllib
from dataclasses import dataclass
from typing import TYPE_CHECKING

import tomlkit

from lem.kernel import files, locks
from lem.settings import places, reading, words

if TYPE_CHECKING:
    from pathlib import Path

    from tomlkit.toml_document import TOMLDocument

# The first line of a file that `set` makes, by its place.
FIRST = (
    (
        places.Scope.local,
        "This machine's own settings for Lem, for this repository. Not committed.",
    ),
    (
        places.Scope.home,
        "Your own settings for Lem, for every repository on this machine.",
    ),
    (places.Scope.machine, "This machine's own settings, for every repository on it."),
)


def first_line(scope: places.Scope) -> str:
    """The comment a new file of `scope` opens with."""
    return next(line for one, line in FIRST if one == scope)


def document(text: str, scope: places.Scope) -> TOMLDocument:
    """The file's text as tomlkit reads it; a new file opens with Lem's first line."""
    if text.strip():
        return tomlkit.parse(text)
    made = tomlkit.document()
    made.add(tomlkit.comment(first_line(scope)))
    made.add(tomlkit.nl())
    return made


def changed(doc: TOMLDocument, table: str, key: str, given: words.Typed | None) -> str:
    """The text with `table.key` set to `given`, or taken out with None, and a table left
    with no key taken out too."""
    held = doc.get(table)
    if given is None and held is not None:
        held.pop(key, None)
        if not held:
            doc.pop(table)
    elif given is not None:
        doc.setdefault(table, tomlkit.table())[key] = given
    return tomlkit.dumps(doc)


def only_lems(text: str, scope: places.Scope) -> bool:
    """Whether the text holds nothing but Lem's first line and blank lines."""
    said = {line.strip() for line in text.splitlines()} - {""}
    return said <= {f"# {first_line(scope)}"}


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


def written(edit: Edit, where: reading.Where) -> None:
    """Write `edit` into its file, checked first as `where` reads the file's place."""
    path = edit.path
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    doc = document(text, edit.scope)
    new = changed(doc, edit.table, edit.key, edit.given)
    name = where.named(edit.scope)
    reading.check(tomllib.loads(new), edit.scope, name, where)
    if only_lems(new, edit.scope):
        path.unlink(missing_ok=True)
    elif new != text:
        files.write_whole(path, new.encode("utf-8"))


def applied(edit: Edit, where: reading.Where) -> None:
    """`written` under the file's lock, from the read to the rename."""
    with locks.held(edit.lock):
        written(edit, where)
