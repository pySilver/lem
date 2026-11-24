"""A file written whole: the one writer that `land.py`, `criteria.py`, `project.py`,
`lem_inbox.py` and `experts.py` share.

A reader of a record, a pull request's text or a plan finds the old file or the new
one, never a part: the text goes to a file beside it under another name, which then
replaces it in one rename. The other name is the caller's, and it is part of what the
caller does: two writers of one file at one moment must never write one other file, so
it holds the process's id, and the board server's threads, which share that id, add
their own (`lem_inbox.py`); a check looks for what a writer left (`lem-land-guards.sh`
finds no `whole.txt*.new`). So a caller that has a scheme of its own passes the name,
and the rest take `NAME.PID.new` beside the file. A caller that may write the first
file of a folder says so (`make_folder`); the others write into a folder that is there.

It imports nothing of Lem's, so that any script may load it.
"""

import json
import os
from pathlib import Path


def write_whole(
    file: Path, text: str, *, fresh: Path | None = None, make_folder: bool = False
) -> None:
    """Write TEXT as FILE whole or not at all: under FRESH first, `NAME.PID.new` beside
    FILE unless named, then renamed over FILE. With MAKE_FOLDER, FILE's folder is made
    first when it is not there."""
    if make_folder:
        file.parent.mkdir(parents=True, exist_ok=True)
    staging = fresh or file.with_name(f"{file.name}.{os.getpid()}.new")
    staging.write_text(text, encoding="utf-8")
    staging.replace(file)


def write_json(
    file: Path, data: object, *, fresh: Path | None = None, make_folder: bool = False
) -> None:
    """Write DATA as FILE whole, as JSON in the one form of Lem's records: two spaces
    of indent, every character as itself, and a line end after it."""
    write_whole(
        file,
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        fresh=fresh,
        make_folder=make_folder,
    )
