"""The time of each state of a task that no span holds (`add_block` and `landing` of `time_of` on
`main`): a move starts a state and the next one ends it, and the spans inside it are cut out.

In a build the rest is its coordinator's, in a landing Lem's (`coordinators.py`); in any other
state it is who holds the work in it (`moves.py`).
"""

from typing import TYPE_CHECKING, NamedTuple

from lem.board.views.timeline import coordinators, frame, moves, shapes
from lem.records.journal.task import StateNoted

if TYPE_CHECKING:
    from collections.abc import Iterator
    from datetime import datetime

    from lem.records.record import Record

    type Covers = list[tuple[datetime, datetime]]
    type Piece = tuple[datetime, datetime]
    type Named = tuple[str, str]


class Block(NamedTuple):
    """A state: its move, when it began and ended, and whether it runs now."""

    noted: StateNoted
    start: datetime
    end: datetime
    live: bool


def blocks_of(record: Record, drawn: frame.Frame) -> list[Block]:
    """The task's states, each up to the next move, the last to the drawing's end while the task
    runs."""
    noted = [entry for entry in record.journal if isinstance(entry, StateNoted)]
    ends = [*(entry.at for entry in noted[1:]), None]
    pairs = zip(noted, ends, strict=True)
    return [block_of(entry, end, drawn) for entry, end in pairs]


def block_of(noted: StateNoted, end: datetime | None, drawn: frame.Frame) -> Block:
    """A state up to `end`; with none, a moment once the task ended, else up to now."""
    if end is not None:
        return Block(noted, noted.at, end, live=False)
    if drawn.ended:
        return Block(noted, noted.at, noted.at, live=False)
    return Block(noted, noted.at, drawn.end, live=True)


def rest(record: Record, drawn: frame.Frame, covers: Covers) -> Iterator[shapes.Held]:
    """The time of each state that no stretch of `covers` holds, on the lane of who held it."""
    for block in blocks_of(record, drawn):
        yield from held_in(record, block, covers)


def held_in(record: Record, block: Block, covers: Covers) -> Iterator[shapes.Held]:
    """The uncovered pieces of a state, each on the lane of who held it, with the state's line."""
    what = moves.line_of(record, block.noted)
    for piece in frame.gaps(block.start, block.end, covers):
        named = head_of(record, block, covers, piece)
        if named is not None:
            yield held_piece(block, piece, named, what)


def held_piece(block: Block, piece: Piece, named: Named, what: str) -> shapes.Held:
    """A piece of a state on its lane; the last runs while the state does."""
    begun, ended = piece
    lane, head = named
    live = block.live and ended == block.end
    return shapes.Held(lane, begun, ended, head, what, live=live)


def head_of(
    record: Record, block: Block, covers: Covers, piece: tuple[datetime, datetime]
) -> tuple[str, str] | None:
    """The lane and head of a piece of a state: a build's coordinator, Lem in a landing, or who
    holds the work in the state."""
    noted = block.noted
    inside = [cover for cover in covers if block.start <= cover[0] < block.end]
    if noted.hold is None and noted.status == "building":
        return coordinators.built(record, inside, piece[1])
    if noted.hold is None and noted.status == "landing":
        return shapes.LEM, coordinators.landed(inside, piece, live=block.live)
    return moves.held_by(record, noted)
