"""The fast track end to end in its one session: the request opens the task's own session, its
first line says that nothing waits for the owner, the same session takes the fast phase to the
merge, and it closes once the task ended. The landing's own steps, cuts and stops are
`tests/journeys/test_skeleton.py`'s; this journey adds the session around them.
"""

from typing import TYPE_CHECKING

import pytest

from fakes.repo import run_git
from fakes.terminal import FakeTerminal
from journeys.agent import ok, small_built, small_landed
from journeys.test_skeleton import SLUG, SUBJECT, made
from lem.app import wiring
from lem.ports.place import Place
from lem.ports.terminal import Pane

if TYPE_CHECKING:
    from pathlib import Path

type Capsys = pytest.CaptureFixture[str]


def test_a_fast_task_goes_from_its_request_to_its_merge_in_one_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    place = Place(checkout=world.checkout, home=tmp_path, environ={})
    terminal = wiring.bound(place).terminal
    assert isinstance(terminal, FakeTerminal)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "claude"))
    caller = Pane(id="S-MINE", name="main", workspace="W-1")
    terminal.panes[caller.id] = caller
    terminal.caller = caller.id
    ok(capsys, world, "task", "open", SLUG, "--ask", "the README says recieve")
    opened = ok(capsys, world, "session", "open", SLUG, "--why", "new")["result"]
    assert (opened["phase"], opened["already"]) == ("shape", False)
    assert opened["workspace"] == caller.workspace
    terminal.caller = opened["session"]
    files = {"README.md": "The README says receive.\n"}
    small_built(capsys, world, SLUG, files, SUBJECT, opened=True)
    first = ok(capsys, world, "session", "wait", SLUG, "--first-line")["result"]
    assert "Fast track" in first["say"]
    (row,) = ok(capsys, world, "session", "list")["result"]
    assert (row["session"], row["phase"], row["live"]) == (
        opened["session"],
        "fast",
        True,
    )
    assert ok(capsys, world, "waiting")["result"]["count"] == 0
    small_landed(capsys, world, SLUG, SUBJECT)
    assert world.record()["task"]["status"] == "landed"
    assert (
        run_git(world.repo.origin, "show", "main:README.md")
        == "The README says receive."
    )
    closed = ok(capsys, world, "session", "close", SLUG, "--why", "ended")["result"]
    assert (closed["session"], closed["closed"]) == (opened["session"], True)
    assert terminal.closed == [opened["session"]]
    assert [one.name for one in terminal.openings] == [SLUG]
