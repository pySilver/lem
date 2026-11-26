"""A task and its agterm overlay, with neither agterm nor a server started."""

import json
from dataclasses import dataclass, field
from subprocess import CompletedProcess
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from fakes import records
from fakes.terminal import FakeTerminal
from lem.adapters import agterm_ctl
from lem.app.asking import live
from lem.app.sessions import acts, log
from lem.ports.terminal import Pane
from lem.store import tasks
from unit.board.service.given import Board, made

if TYPE_CHECKING:
    from collections.abc import Iterator
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

    def ctl(self, _env: dict, *words: str, **_flags: object) -> CompletedProcess[str]:
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
        return self.other(words)

    def other(self, words: tuple[str, ...]) -> CompletedProcess[str]:
        if words[0] == "tree":
            overlays = [{"id": PAGE, "file": self.shown}] if self.shown else []
            found = {"id": SESSION, "htmlOverlays": overlays}
            return self.reply(words, {"tree": {"workspaces": [{"sessions": [found]}]}})
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
def task_terminal() -> FakeTerminal:
    return FakeTerminal(
        panes={SESSION: Pane(id=SESSION, name=SLUG)},
        grounds={SESSION: ("claude",)},
    )


@pytest.fixture
def board(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, task_terminal: FakeTerminal
) -> Iterator[Board]:
    """A workspace with a task whose current session is the overlay stand-in."""
    board = made(tmp_path, None)
    tasks.create(board.state, records.record(SLUG, status="shaping"))
    log.append(
        board.state / "tasks" / SLUG,
        acts.Open(
            at=records.MOMENT, session=SESSION, name=SLUG, phase="shape", why="open"
        ),
    )
    monkeypatch.setenv("LEM_TASK", SLUG)
    monkeypatch.chdir(board.checkout)
    with patch.object(live, "bound") as bound:
        bound.return_value.terminal = task_terminal
        yield board
        assert task_terminal.told == task_terminal.closed == task_terminal.shown == []
