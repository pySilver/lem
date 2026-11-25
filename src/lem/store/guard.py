"""What the store may read and write: a state folder of this Lem's form, and, under the test
entry, nothing outside the test's own folder (`lem.kernel.folders` holds the marker and the
rule).

A state folder that holds the files of the Lem before (0.3: `events.jsonl`, task folders with
no `task.json`) is neither read nor written: every function of the store passes here first.
"""

from typing import TYPE_CHECKING

from lem.kernel import folders

if TYPE_CHECKING:
    from pathlib import Path

# What an empty state folder may hold: the ignore file that hides it from git.
EMPTY = frozenset((".gitignore",))
WHAT = "the state folder"


def form(state: Path) -> str:
    """The form of a state folder: `new`, `empty` or `old`."""
    return folders.form(state, EMPTY)


def readable(state: Path) -> str:
    """The form of `state`, refused when it is the state of the Lem before."""
    folders.inside_test_root(state)
    found = form(state)
    if found == "old":
        raise folders.older(state, WHAT)
    return found


def writable(state: Path) -> None:
    """Make `state` a state folder of this form before a write: refused when it holds the
    files of the Lem before, given its marker and ignore file when absent or empty."""
    folders.marked(state, EMPTY, WHAT)
    ignore = state / ".gitignore"
    if not ignore.is_file():
        ignore.write_text("*\n", encoding="utf-8")
