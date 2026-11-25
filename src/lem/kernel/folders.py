"""The two folders of Lem that the Lem before also wrote, a repository's `.lem/state/` and Lem's
home folder, and the marker that tells this Lem's folder from the Lem before's.

A folder this Lem made holds the marker `lem-state.json`, which its first write publishes into
the folder when it is absent or empty. A folder that holds anything else and no marker holds the
files of Lem 0.3 (`events.jsonl` and task folders with no `task.json`; `owner.jsonl`,
`serve.lock`, `serve.log`, `push.json` in the home): this Lem writes nothing into it. The owner's
ruling: "The release of the reshape reads no record of the Lem before it: his repositories start
over"; the move of the old files is his act at the cutover, which `lem doctor` names.

The test entry names its temporary root in `LEM_TEST_ROOT`; while it is set, a folder outside it
is a fault, so that no test reaches the real state or home that the owner's board server reads.
"""

import os
from pathlib import Path
from typing import TYPE_CHECKING

from lem.kernel import files, paths
from lem.kernel.errors import Fault, Refusal

if TYPE_CHECKING:
    from collections.abc import Mapping

MARKER = "lem-state.json"
FORM = b'{"form": 1}\n'
# The variable the test entry sets to its temporary root.
TEST_ROOT = "LEM_TEST_ROOT"


def inside_test_root(path: Path) -> None:
    """Fault when a test reaches `path` outside its own temporary root."""
    root = os.environ.get(TEST_ROOT)
    if root and not path.resolve().is_relative_to(Path(root).resolve()):
        raise Fault(
            f"a test reached {path}, outside its own folder {root}: give it a repository "
            "and a home of its own (tests/fakes/repo.py, the entry's HOME)"
        )


def form(folder: Path, empty: frozenset[str]) -> str:
    """`new` with the marker; `empty` when absent or holding only the names `empty`; else
    `old`, a folder of the Lem before."""
    if (folder / MARKER).is_file():
        return "new"
    if not folder.is_dir():
        return "empty"
    held = {entry.name for entry in folder.iterdir()}
    return "empty" if held <= empty else "old"


def older(folder: Path, what: str) -> Refusal:
    """The refusal of a folder of the Lem before: `what` names the folder for the owner."""
    return Refusal(
        "old-state",
        f"{what} {folder} holds the files of Lem 0.3; the new Lem starts from an empty "
        "folder",
        "the owner's cutover moves the old files away (lem doctor names them); until then "
        "this machine runs the Lem it has",
    )


def marked(folder: Path, empty: frozenset[str], what: str) -> None:
    """Make `folder` a folder of this Lem before a write: refused when it holds the files of
    the Lem before, given the marker when absent or empty."""
    inside_test_root(folder)
    found = form(folder, empty)
    if found == "old":
        raise older(folder, what)
    if found == "empty":
        folder.mkdir(parents=True, exist_ok=True)
        files.publish(folder / MARKER, FORM)


def home_marked(home: Path) -> Path:
    """`home`, made a home folder of this Lem before a write, else refused."""
    marked(home, frozenset(), "Lem's home folder")
    return home


def home_for_writing(environ: Mapping[str, str]) -> Path:
    """Lem's home folder, for a write: every writer of the home calls this (the board's files,
    the machine's settings, the owner's presence, the log), so none writes beside the files
    of the Lem before."""
    return home_marked(paths.home(environ))
