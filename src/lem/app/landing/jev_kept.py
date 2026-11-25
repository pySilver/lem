"""Jev's reads that a landing keeps, so that no finding is sent twice, by this run or the next
(`alike` and `jev` of `landing.json` on `main`): for each finding's digest, the score of each
item it was asked about, None for an item Jev gave no score.

A stand-in, `tasks/SLUG/jev.json` written whole, until the task's record has a field for them
(`notes/land-review.md`).
"""

from typing import TYPE_CHECKING

import msgspec

from lem.kernel import files

if TYPE_CHECKING:
    from pathlib import Path

NAME = "jev.json"
type Scores = dict[str, float | None]


class Kept(msgspec.Struct, kw_only=True):
    """Jev's reads of whether a finding is the same defect as an item, by the finding."""

    alike: dict[str, Scores] = msgspec.field(default_factory=dict)


def read(folder: Path) -> Kept:
    """The reads kept in the task's folder; none when there are none."""
    path = folder / NAME
    if not path.is_file():
        return Kept()
    return msgspec.json.decode(path.read_bytes(), type=Kept)


def write(folder: Path, kept: Kept) -> None:
    """Keep the reads, whole."""
    files.write_whole(folder / NAME, msgspec.json.encode(kept))
