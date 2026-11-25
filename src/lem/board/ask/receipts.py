"""An immutable answer payload that the task can cite by its timestamp."""

from datetime import timedelta
from typing import TYPE_CHECKING

import msgspec

from lem.board.ask import keys
from lem.kernel import files, locks

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path

type Payload = dict[str, object]


def kept(folder: Path, at: datetime, payload: Payload) -> datetime:
    """Give each attempt its own time key, even when the clock repeats."""
    encoded = msgspec.json.encode(payload)
    with locks.held(folder / "answer.lock"):
        named = vacant(folder, at)
        files.publish(keys.answer_at(folder, named), encoded)
    return named


def vacant(folder: Path, at: datetime) -> datetime:
    """The first unused receipt time at or after the time of the answer."""
    tick = timedelta(microseconds=1)
    while keys.answer_at(folder, at).exists():
        at += tick
    return at


def read(folder: Path, at: datetime) -> Payload:
    """The payload of the answer cited in the task."""
    path = keys.answer_at(folder, at)
    return msgspec.json.decode(path.read_bytes(), type=Payload)
