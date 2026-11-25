"""A Claude Code transcript read from its end, for the `Harness` port on Claude Code
(`harness_claude`).

The newest records are at a transcript's end, and a long session's transcript runs to many
megabytes, so the signs read it from its end, a block at a time, and stop at the first record
that answers (`claude_turns`). A file that does not read gives no sign and no turn.
"""

from contextlib import closing, contextmanager
from typing import TYPE_CHECKING

from lem.adapters import claude_transcript, claude_turns

if TYPE_CHECKING:
    from collections.abc import Generator, Iterator
    from datetime import datetime
    from pathlib import Path

# How much of a file is read at a time from its end, in bytes (`signs.BLOCK` on `main`, a guess).
BLOCK = 65536


def tail_lines(path: Path, block: int = BLOCK) -> Generator[bytes]:
    """The lines of the file from its end to its start, read `block` bytes at a time."""
    with path.open("rb") as stream:
        end = stream.seek(0, 2)
        rest = b""
        while end > 0:
            start = max(0, end - block)
            stream.seek(start)
            lines = (stream.read(end - start) + rest).split(b"\n")
            end = start
            # The first piece may be the end of a line that starts in the block before.
            rest = lines.pop(0) if start else b""
            yield from reversed(lines)


@contextmanager
def newest_first(path: Path) -> Generator[Iterator[claude_transcript.Entry]]:
    """The records of the file, newest first, read as they are reached; the file is closed
    when the block ends."""
    lines = tail_lines(path)
    with closing(lines):
        yield claude_transcript.entries(lines)


def file_sign(path: Path) -> datetime | None:
    """The newest sign of the transcript at `path`; None when it does not read."""
    try:
        with newest_first(path) as records:
            return claude_turns.newest_sign(records)
    except OSError:
        return None


def file_turn(path: Path) -> claude_turns.Turn | None:
    """Whether the newest turn of the transcript at `path` runs; None when it does not read."""
    try:
        with newest_first(path) as records:
            return claude_turns.turn_of(records)
    except OSError:
        return None
