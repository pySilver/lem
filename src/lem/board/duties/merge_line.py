"""How many approved tasks wait at each server call to merge: one framed line of
`merge-line.jsonl` in the state folder for each (the owner's choice of 2026-11-25, the merge
line: "the board server records, at each merge, how many approved tasks wait").

A task is approved while its merge is the server's to make (`merging.merge_wait` gives
`merges`): the merge agent's `merge` for a request it may merge, the owner's merge that stands,
or a call the forge queued. The line counts the others, besides the task that merges. Lem's
events of 2026-11-17 to 24 (88 landings) had no other task waiting at 44, one at 25 and two or
more at 19; an agent that sets the order is worth its cost when this file shows many merges
with three or more waiting.

A writer appends a line end, the JSON and a line end in one `os.write`, so two writers never
mix their bytes; a reader skips an empty line and a damaged one.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.kernel import files
from lem.records.base import Frozen, Moment, Sha, Slug
from lem.records.landing.merge import Merger
from lem.store import guard

if TYPE_CHECKING:
    from pathlib import Path


LINE = "merge-line.jsonl"


class Waited(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """One merge the server started: when, the task, its tip, who merges, and the approved
    tasks that waited besides it, with their count."""

    at: Moment
    task: Slug
    tip: Sha
    by: Merger
    waiting: int
    behind: tuple[Slug, ...]


def noted(state: Path, waited: Waited) -> None:
    """Append one merge's line to the state folder's file."""
    guard.writable(state)
    files.append_frame(state / LINE, msgspec.json.encode(waited))


def read(state: Path) -> tuple[Waited, ...]:
    """Every readable line of the file, in the order written."""
    guard.readable(state)
    try:
        body = (state / LINE).read_bytes()
    except FileNotFoundError:
        return ()
    found = (decoded(raw) for raw in body.split(b"\n") if raw.strip())
    return tuple(one for one in found if one is not None)


def decoded(raw: bytes) -> Waited | None:
    """One line, or None when it is damaged."""
    try:
        return msgspec.json.decode(raw, type=Waited)
    except msgspec.DecodeError:
        return None
