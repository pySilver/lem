"""The board server's last look at the forge, `forge.json` in the state folder, as the list of
what waits reads it (`board_model.forge_look` and `conflicts` on `main`).

The server's forge duty writes it; this is its form: when it looked, and for each task with an
open pull request the head the forge saw and whether the forge can merge it. The forge calls a
request conflicting only at the head Lem proposed last, so a head the task moved since counts for
nothing. No file is no look yet.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.kernel.errors import Fault
from lem.records.base import Frozen, Moment, Sha, Slug

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record

LOOK = "forge.json"
CONFLICTING = "CONFLICTING"


class Seen(Frozen, frozen=True, kw_only=True):
    """What the forge said of one task's pull request: its head, and GitHub's `mergeable`."""

    head: Sha
    mergeable: str | None = None


class Look(Frozen, frozen=True, kw_only=True):
    """The server's last look at the forge: when, and each task's pull request."""

    looked: Moment | None = None
    seen: dict[Slug, Seen] = msgspec.field(default_factory=dict)


def read(state: Path) -> Look:
    """The last look; no file is none yet."""
    path = state / LOOK
    try:
        return msgspec.json.decode(path.read_bytes(), type=Look)
    except FileNotFoundError:
        return Look()
    except msgspec.DecodeError as error:
        raise Fault(
            f"{path} is no look of the board's server at the forge: {error}"
        ) from error


def conflicts(look: Look, record: Record) -> bool:
    """Whether the forge calls the task's pull request conflicting at the head Lem proposed."""
    seen = look.seen.get(record.task.slug)
    proposed = record.landing.proposed if record.landing else None
    if seen is None or proposed is None:
        return False
    return seen.mergeable == CONFLICTING and seen.head == proposed.tip
