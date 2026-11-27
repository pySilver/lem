"""The board's update notice: the release the last board server ran, the notice of a server
that starts with a higher one until a visible page of the board takes it, and the releases the
owner saw (the record is `lem.board.update_record`).

Each server records its release at its start, so a notice comes after a swap and after a start
that follows a stop alike. A fault of the record at a start goes to `lem.log` and the server
starts; a page then shows its line, and the next start tries again.
"""

import sys
from typing import TYPE_CHECKING

import msgspec

from lem.board import update_record
from lem.kernel import logs, release
from lem.kernel.errors import Fault

if TYPE_CHECKING:
    from pathlib import Path


def opened(state: update_record.State, version: str) -> update_record.State:
    """The state after a server of `version` starts: a release higher than the last one that
    the owner has not seen gets the notice, with the last one as the release it replaced."""
    last = state.last_version
    pending = state.pending
    if (
        last is not None
        and release.newer(version, last)
        and version not in state.seen_versions
    ):
        pending = update_record.Notice(version=version, previous_version=last)
    return msgspec.structs.replace(state, pending=pending, last_version=version)


def started(home: Path, version: str) -> None:
    """Record the release of a server that starts, before it serves a page."""
    with update_record.changing(home):
        state = update_record.read(home)
        after = opened(state, version)
        if after != state:
            update_record.written(home, after)


def at_start(home: Path, version: str) -> None:
    """Record the release of a server that starts. The note is a courtesy: a fault of its
    record goes to `lem.log`, the file stays as it is, and the server starts."""
    try:
        started(home, version)
    except Fault as error:
        logged(home, error)


def logged(home: Path, error: Fault) -> None:
    """Append the fault's traceback to `lem.log`, else to standard error, which `serve.log`
    takes."""
    argv = sys.argv[1:]
    try:
        logs.fault(home / logs.LOG, error, argv)
    except OSError:
        sys.stderr.write(logs.entry(error, argv))


def swapped(home: Path, previous: str) -> None:
    """Record the release of the server that a newer install stops, for the start after it:
    a record that the release before this one never wrote then names it too."""
    with update_record.changing(home):
        state = update_record.read(home)
        update_record.written(
            home, msgspec.structs.replace(state, last_version=previous)
        )


def seen(home: Path, version: str) -> update_record.Notice | None:
    """Give the notice once, to the first page that asks while it is visible."""
    if update_record.read(home).pending is None:
        return None
    with update_record.changing(home):
        state = update_record.read(home)
        notice = state.pending
        if notice is None or notice.version != version:
            return None
        seen_versions = (*state.seen_versions, version)
        update_record.written(
            home,
            msgspec.structs.replace(state, pending=None, seen_versions=seen_versions),
        )
        return notice
