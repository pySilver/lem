"""The sessions of an ended task can keep its files after its journal falls quiet."""

from typing import TYPE_CHECKING, Literal

import msgspec

from lem.records.base import Frozen, Moment
from lem.store import places, sessions
from lem.store.retention import rules

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record

ACTS = "session-acts.jsonl"


class Timed(Frozen, frozen=True, kw_only=True, forbid_unknown_fields=False):
    """The kind and moment from a session act's frame."""

    kind: Literal["open", "close", "wake", "stopped", "worked"]
    at: Moment


def decoded(raw: bytes) -> Moment | None:
    """The moment of a readable session act."""
    try:
        return msgspec.json.decode(raw, type=Timed).at
    except msgspec.DecodeError:
        return None


def acted(path: Path) -> tuple[Moment, ...]:
    """The moments of the session acts, without a link followed."""
    if path.is_symlink():
        return ()
    try:
        frames = path.read_bytes().splitlines()
    except FileNotFoundError:
        return ()
    moments = map(decoded, frames)
    return tuple(one for one in moments if one is not None)


def active(folder: Path, cutoff: Moment) -> bool:
    """Whether a session start or a session act is newer than the cutoff."""
    if any(moment > cutoff for moment in acted(folder / ACTS)):
        return True
    if (folder / sessions.SESSIONS).is_symlink():
        return False
    return any(one.at > cutoff for one in sessions.read(folder))


def call_of(state: Path, record: Record, cutoff: Moment) -> rules.Call:
    """The task's retention class, with its session activity included."""
    call = rules.call_of(record, cutoff)
    folder = places.task_folder(state, record.task.slug)
    return "young" if call == "old" and active(folder, cutoff) else call
