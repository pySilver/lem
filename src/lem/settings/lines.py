"""Lem's own lines in a settings file that `set` makes: the comment a new file opens with, which
says whose file it is, and the test of a file left with nothing else, which then goes."""

from typing import TYPE_CHECKING

import tomlkit

from lem.settings import places

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


def only_lems(text: str, scope: places.Scope) -> bool:
    """Whether the text holds nothing but Lem's first line and blank lines."""
    said = {line.strip() for line in text.splitlines()} - {""}
    return said <= {f"# {first_line(scope)}"}


def text_of(path: Path) -> str:
    """The text of a settings file; empty when it is not there."""
    return path.read_text(encoding="utf-8") if path.is_file() else ""
