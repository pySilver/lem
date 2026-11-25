"""What the store may read and write: a state folder of this Lem's form, and, under the test
entry, nothing outside the test's own folder.

A state folder of this Lem's form holds the marker `lem-state.json`, which the first write of
the store publishes into an absent or empty folder. A folder that holds anything else and no
marker is the state of the Lem before (0.3: `events.jsonl`, task folders with no `task.json`):
the store reads nothing of it and writes nothing into it. The owner's ruling: "The release of
the reshape reads no record of the Lem before it: his repositories start over"; the move of the
old state is his act at the cutover.

The test entry names its temporary root in `LEM_TEST_ROOT`; while it is set, a workspace or a
state folder outside that root is a fault, so that no test reaches the state of the checkout it
runs in, which the owner's board server reads.
"""

import os
from pathlib import Path

from lem.kernel import files
from lem.kernel.errors import Fault, Refusal

MARKER = "lem-state.json"
FORM = b'{"form": 1}\n'
# The variable the test entry sets to its temporary root.
TEST_ROOT = "LEM_TEST_ROOT"
# What an empty state folder may hold: the ignore file that hides it from git.
EMPTY = frozenset((".gitignore",))


def inside_test_root(path: Path) -> None:
    """Fault when a test reaches `path` outside its own temporary root."""
    root = os.environ.get(TEST_ROOT)
    if root and not path.resolve().is_relative_to(Path(root).resolve()):
        raise Fault(
            f"a test reached {path}, outside its own folder {root}: give it a repository "
            "of its own (tests/fakes/repo.py)"
        )


def form(state: Path) -> str:
    """`new` with the marker, `empty` when absent or empty, else `old`."""
    if (state / MARKER).is_file():
        return "new"
    if not state.is_dir():
        return "empty"
    held = {entry.name for entry in state.iterdir()}
    return "empty" if held <= EMPTY else "old"


def readable(state: Path) -> str:
    """The form of `state`, refused when it is the state of the Lem before."""
    inside_test_root(state)
    found = form(state)
    if found == "old":
        raise Refusal(
            "old-state",
            f"this repository holds the state of Lem 0.3 in {state}; the new Lem starts "
            "from an empty state folder",
            "the owner's cutover moves the old state away (lem doctor names it); until "
            "then this repository runs the Lem it has",
        )
    return found


def writable(state: Path) -> None:
    """Make `state` a state folder of this form before a write: refused when it is the state
    of the Lem before, given its marker and ignore file when absent or empty."""
    if readable(state) == "new":
        return
    state.mkdir(parents=True, exist_ok=True)
    ignore = state / ".gitignore"
    if not ignore.is_file():
        files.publish(ignore, b"*\n")
    files.publish(state / MARKER, FORM)
