"""`FakeTerminal`: the `Terminal` port over sessions a test holds, with every act recorded.

A session Lem opens never takes the focus: only `select`, the owner's act, changes the selected
session. `unreadable` makes the list unreadable, as an agterm that does not answer.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.ports.faults import Unanswered
from lem.ports.terminal import Mark, Opening, Pane, ShowMode, Unreadable

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class FakeTerminal:
    """Sessions, and what Lem did to them."""

    panes: dict[str, Pane] = field(default_factory=dict)
    openings: list[Opening] = field(default_factory=list)
    told: list[tuple[str, str]] = field(default_factory=list)
    marks: dict[str, Mark] = field(default_factory=dict)
    shown: list[tuple[str, str, ShowMode]] = field(default_factory=list)
    closed: list[str] = field(default_factory=list)
    unreadable: str | None = None
    picked: str | None = None

    def known(self, session: str) -> Pane:
        """The session `session`, or the fault agtermctl gives for one that is gone."""
        if session not in self.panes:
            raise Unanswered("agtermctl", f"no session {session}")
        return self.panes[session]

    def sessions(self) -> tuple[Pane, ...] | Unreadable:
        if self.unreadable is not None:
            return Unreadable(why=self.unreadable)
        return tuple(self.panes.values())

    def open(self, opening: Opening) -> str:
        if opening.companion_of is not None:
            self.known(opening.companion_of)
        session = f"session-{len(self.openings) + 1}"
        self.openings.append(opening)
        self.panes[session] = Pane(
            id=session, name=opening.name, cwd=opening.cwd, workspace=opening.workspace
        )
        return session

    def close(self, session: str, *, when_unselected: bool) -> None:
        pane = self.known(session)
        if when_unselected and pane.selected:
            return
        del self.panes[session]
        self.closed.append(session)

    def tell(self, session: str, line: str) -> None:
        self.known(session)
        self.told.append((session, line))

    def mark(self, session: str, status: Mark) -> None:
        self.known(session)
        self.marks[session] = status

    def show(self, session: str, url: str, mode: ShowMode) -> None:
        self.known(session)
        self.shown.append((session, url, mode))

    def select(self, session: str) -> None:
        self.known(session)
        for name, pane in self.panes.items():
            self.panes[name] = replace(pane, selected=name == session)

    def picker(self, rows: tuple[str, ...], cwd: Path) -> str | None:
        return self.picked if self.picked in rows else None
