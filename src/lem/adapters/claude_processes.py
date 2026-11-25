"""The Claude Code process of a transcript and the commands it runs, for the `Harness` port on
Claude Code (`harness_claude`).

A transcript is `FOLDER/projects/NAME/ID.jsonl`. The process of a Claude Code session is
`FOLDER/sessions/PID.json`, with `pid` and `sessionId`, in the folder that holds the transcript,
never one found from this process's own `CLAUDE_CONFIG_DIR`. Its children in the process table
are what it runs now: a command of the Bash tool, a background one and a subagent's too, a
hook's process, `caffeinate` (read on the owner's Mac with Claude Code 2.1.330, 2026-11-22:
`signs.py` on `main`). The process table is psutil's, behind `Table`, so that a test gives its
own.
"""

from typing import TYPE_CHECKING, Protocol, Self

import msgspec
import psutil

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


class Table(Protocol):
    """The machine's process table, read for one process at a time."""

    def children(self, pid: int) -> tuple[str, ...] | None:
        """The command lines of the direct children of the process `pid`; None when it is
        gone or the table does not read."""
        ...


class Machine:
    """The process table of this machine, through psutil."""

    def children(self, pid: int) -> tuple[str, ...] | None:
        """The command lines of the direct children of the process `pid`; None when it is
        gone or the table does not read."""
        try:
            found = psutil.Process(pid).children()
        except psutil.Error, OSError:
            return None
        return tuple(command_line(child) for child in found)


class ProcessFile(msgspec.Struct, frozen=True, kw_only=True):
    """A Claude Code process file: the pid and the session it runs."""

    pid: int
    session: str = msgspec.field(name="sessionId")

    @classmethod
    def read(cls, path: Path) -> Self | None:
        """The process file at `path`; None when it does not read."""
        try:
            return msgspec.json.decode(path.read_bytes(), type=cls)
        except OSError, msgspec.DecodeError:
            return None


def command_line(process: psutil.Process) -> str:
    """The command line of a process, its words joined by spaces; empty when it has gone or
    does not read."""
    try:
        words = process.cmdline()
    except psutil.Error, OSError:
        return ""
    return " ".join(words)


def folder_of(transcript: Path) -> Path | None:
    """The Claude Code folder of a transcript `FOLDER/projects/NAME/ID.jsonl`, or None for a
    path that is not in that form."""
    parents = transcript.parents
    if not parents[2:] or parents[1].name != "projects":
        return None
    return parents[2]


def pids_of(transcript: Path, claude: str) -> frozenset[int]:
    """The pids that the process files of the transcript's folder give the session `claude`;
    a file that does not read names none."""
    folder = folder_of(transcript)
    files: Iterable[Path] = (
        sorted((folder / "sessions").glob("*.json")) if folder else ()
    )
    found = (ProcessFile.read(path) for path in files)
    return frozenset(each.pid for each in found if each and each.session == claude)


def children(table: Table, pids: frozenset[int]) -> tuple[str, ...] | None:
    """The command lines of the direct children of those of `pids` that live; None when none
    lives or the table does not read: with no process there is no evidence that no shell
    runs."""
    found = (table.children(pid) for pid in sorted(pids))
    alive = [each for each in found if each is not None]
    if not alive:
        return None
    return tuple(command for each in alive for command in each)
