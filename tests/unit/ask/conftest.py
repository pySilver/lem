"""A task and its agterm overlay, with neither agterm nor a server started."""

import json
import os
from dataclasses import dataclass, field
from subprocess import CompletedProcess
from typing import TYPE_CHECKING

import pytest

from fakes import records
from lem.adapters import agterm_ctl
from lem.app.sessions import acts, log
from lem.board import opening
from lem.store import tasks
from unit.board.service.given import Board, made

if TYPE_CHECKING:
    from pathlib import Path

SLUG = "keep-a-dash"
SESSION = "S1"
PAGE = "P1"


@dataclass
class Agterm:
    """The commands this case asks of agterm, and the page it reports."""

    shown: str | None = None
    outcome: str | None = None
    payload: str | None = None
    error: str | None = None
    calls: list[tuple[str, ...]] = field(default_factory=list)
    silent: bool = False
    grounds: dict[str, tuple[str, ...]] = field(
        default_factory=lambda: {SESSION: ("zsh",)}
    )

    def ctl(self, env: dict, *words: str, **_flags: object) -> CompletedProcess[str]:
        self.calls.append(words)
        if self.silent:
            return CompletedProcess(words, 1, "", "no socket")
        if words[:3] == ("session", "overlay", "open"):
            if self.shown:
                return self.reply(words, error="overlay already open")
            self.shown = words[words.index("--html") + 1]
            return self.reply(words, {"pageID": PAGE})
        if words[:3] == ("session", "overlay", "result"):
            outcome = self.outcome or "pending"
            return self.reply(
                words,
                {"pageOutcome": {"outcome": outcome, "value": self.payload}},
                status={"submitted": 0, "pending": 1, "dismissed": 2}[outcome],
                error=self.error,
            )
        if words[:3] == ("session", "overlay", "close"):
            self.shown = None
            return self.reply(words)
        return self.other(words, env.get("AGTERM_WINDOW_ID"))

    def other(
        self, words: tuple[str, ...], window: str | None
    ) -> CompletedProcess[str]:
        if words[0] == "tree":
            overlays = [{"id": PAGE, "file": self.shown}] if self.shown else []
            found = [
                {"id": session, "foreground": ground, "htmlOverlays": overlays}
                for session, ground in self.grounds.items()
                if window is None or window == session
            ]
            return self.reply(
                words, {"tree": {"workspaces": [{"id": "W1", "sessions": found}]}}
            )
        if words[:2] == ("session", "status"):
            return self.reply(words)
        raise AssertionError(words)

    @staticmethod
    def reply(
        words: tuple[str, ...],
        result: dict | None = None,
        *,
        error: str | None = None,
        status: int = 0,
    ) -> CompletedProcess[str]:
        body = {"ok": error is None, "result": result or {}, "error": error}
        return CompletedProcess(words, 1 if error else status, json.dumps(body), "")


@pytest.fixture
def terminal(monkeypatch: pytest.MonkeyPatch) -> Agterm:
    """An agterm session and its fake command, confined to this test."""
    stand_in = Agterm()
    monkeypatch.setenv("AGTERM_ENABLED", "1")
    monkeypatch.setenv("AGTERM_SESSION_ID", SESSION)
    monkeypatch.setattr(agterm_ctl, "ctl", stand_in.ctl)
    return stand_in


@pytest.fixture
def board(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, terminal: Agterm) -> Board:
    """A workspace with a task whose current session is the overlay stand-in."""
    terminal.grounds[SESSION] = ("claude",)
    board = made(tmp_path, None)
    board.app.state.environ = dict(os.environ)
    opening.detached(board.app.state.environ)
    tasks.create(board.state, records.record(SLUG, status="shaping"))
    log.append(
        board.state / "tasks" / SLUG,
        acts.Open(
            at=records.MOMENT, session=SESSION, name=SLUG, phase="shape", why="open"
        ),
    )
    monkeypatch.setenv("LEM_TASK", SLUG)
    monkeypatch.chdir(board.checkout)
    return board
