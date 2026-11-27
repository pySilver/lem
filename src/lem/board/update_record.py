"""`serve-update.json` in Lem's home folder: the board's update record, which `lem.board.update`
changes. A file of its own, which no other part of Lem reads: `serve.json` goes at each clean
stop. A record that does not read, or a home folder the server cannot write, is a fault.
"""

from contextlib import contextmanager
from typing import TYPE_CHECKING

import msgspec

from lem.kernel import files, folders, locks
from lem.kernel.errors import Fault

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

STATE = "serve-update.json"
LOCK = "serve-update.lock"


class Notice(msgspec.Struct, frozen=True, kw_only=True):
    """The installed release and the release it replaced."""

    version: str
    previous_version: str


class State(msgspec.Struct, frozen=True, kw_only=True):
    """The notice that waits, the versions the owner already saw, and the release the last
    server ran (None before the first start)."""

    pending: Notice | None = None
    seen_versions: tuple[str, ...] = ()
    last_version: str | None = None


def read(home: Path) -> State:
    """The update state, empty before the first start."""
    path = home / STATE
    try:
        return msgspec.json.decode(path.read_bytes(), type=State)
    except FileNotFoundError:
        return State()
    except (OSError, msgspec.DecodeError) as error:
        raise Fault(
            f"the board's update record {path} does not read: {error}"
        ) from error


@contextmanager
def changing(home: Path) -> Iterator[None]:
    """Hold the update lock while the record changes; an error of the disk is a fault that
    names the record."""
    record = home / STATE
    try:
        with locks.held(folders.home_marked(home) / LOCK):
            yield
    except OSError as error:
        raise Fault(
            f"the board could not write its update record {record}: {error}"
        ) from error


def written(home: Path, state: State) -> None:
    """Write the update state whole; under `changing`, which takes the lock."""
    files.write_whole(home / STATE, msgspec.json.encode(state))
