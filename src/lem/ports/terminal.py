"""The `Terminal` port: the sessions of agterm (the design's part 4).

A session Lem opens never takes the focus, and a companion opens beside its session; only the
owner's own act selects one. A list that could not be read is `Unreadable`, never an empty list:
the session guard tells the two apart (`surfaces.md` B).
"""

from typing import TYPE_CHECKING, Literal, Protocol

from lem.records.base import Frozen

if TYPE_CHECKING:
    from pathlib import Path


class Pane(Frozen, frozen=True, kw_only=True):
    """A session of the terminal: its id, name, folder, workspace, and whether it is the one
    the owner looks at."""

    id: str
    name: str
    cwd: str | None = None
    workspace: str | None = None
    selected: bool = False


class Unreadable(Frozen, frozen=True, kw_only=True):
    """The list of sessions could not be read, and why."""

    why: str


class Opening(Frozen, frozen=True, kw_only=True):
    """A session to open: its name, folder and command, its workspace, and the session it is a
    companion of."""

    name: str
    cwd: str
    command: tuple[str, ...]
    workspace: str | None = None
    companion_of: str | None = None


type Mark = Literal["working", "waiting", "done", "stopped", "none"]
type ShowMode = Literal["overlay", "companion", "browser"]


class TerminalSessions(Protocol):
    """The sessions: list, open, close, a line to one, its mark."""

    def sessions(self) -> tuple[Pane, ...] | Unreadable: ...
    def open(self, opening: Opening) -> str: ...
    def close(self, session: str, *, when_unselected: bool) -> None: ...
    def tell(self, session: str, line: str) -> None: ...
    def mark(self, session: str, status: Mark) -> None: ...


class TerminalScreens(Protocol):
    """What a session shows: a page, the selected session (the owner's act only), a picker."""

    def show(self, session: str, url: str, mode: ShowMode) -> None: ...
    def select(self, session: str) -> None: ...
    def picker(self, rows: tuple[str, ...], cwd: Path) -> str | None: ...


class Terminal(TerminalSessions, TerminalScreens, Protocol):
    """The whole port."""
