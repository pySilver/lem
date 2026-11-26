"""The async Stop hook at the manifest line and against the sessions agterm stand-in."""

import json
import os
import subprocess
import tempfile
from typing import TYPE_CHECKING

import pytest

from contract.agterm_standin import install
from hooks.claude_code import LINES, claude_environ, hooked, workspace
from lem.hooks import raw, stop, stop_agterm

if TYPE_CHECKING:
    from pathlib import Path

    from contract.agterm_standin import Standin

# How long the stop hook may take with its input never closed, in seconds: under `raw.WAIT`,
# the most a hook that reads its event waits for it, so a stop hook that read it would fail here.
ENDS_WITHIN = raw.WAIT * 0.75
SESSION = "S-1"
PAGE = "P-1"
WAIT_WORD = f"{PAGE}.wait.html"
MARK = ["session", "status", "blocked", "--auto-reset", "--target", SESSION]


def test_the_hook_is_silent_outside_agterm() -> None:
    ran = hooked(
        "stop",
        b"{}",
        AGTERM_SESSION_ID="",
        AGTERM_SOCKET="",
        AGT_SESSION_ID="",
        AGT_SOCKET="",
    )
    assert (ran.returncode, ran.stdout, ran.stderr) == (0, b"", b"")


def test_a_stdin_that_stays_open_does_not_keep_the_stop_hook_alive() -> None:
    child = subprocess.Popen(
        ["/bin/sh", "-c", LINES["stop"]],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=claude_environ({}),
        cwd=tempfile.gettempdir(),
    )
    try:
        assert child.wait(timeout=ENDS_WITHIN) == 0
        assert child.stdout is not None
        assert child.stdout.read() == b""
    finally:
        assert child.stdin is not None
        child.stdin.close()
        if child.poll() is None:
            child.kill()
            child.wait()


def setup(tmp_path: Path, name: str = "ask.html") -> tuple[Standin, dict[str, str]]:
    pages = tmp_path / "lem-ask"
    pages.mkdir()
    page = pages / name
    page.touch()
    node = {"id": SESSION, "workspace": "W-1", "status": "active"}
    agterm = install(
        tmp_path / "agterm",
        [{**node, "htmlOverlays": [{"id": PAGE, "file": str(page)}]}],
    )
    return agterm, agterm.environ(
        AGTERM_ENABLED="1",
        AGTERM_SESSION_ID=SESSION,
        AGTERM_SOCKET=str(tmp_path / "agterm.sock"),
        AGTERM_WINDOW_ID="W-1",
        CLAUDE_CODE_SESSION_ATTENDED="1",
        TMPDIR=str(tmp_path),
    )


def test_stop_restores_the_mark_and_stops_after_the_overlay_closes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    agterm, env = setup(tmp_path)
    steps = iter(("first", "active", "closed"))

    def in_parallel(_delay: float) -> None:
        step = next(steps)
        (node,) = agterm.sessions()
        if step == "active":
            node["status"] = "active"
        if step == "closed":
            node["htmlOverlays"] = []
        agterm.change(sessions=[node])

    monkeypatch.setattr(stop_agterm.time, "sleep", in_parallel)
    monkeypatch.setattr(stop_agterm, "gettempdir", lambda: str(tmp_path))
    assert stop.answer(env, None) == ""
    assert agterm.calls().count(MARK) == 2
    assert agterm.calls()[-1] == ["tree", "--json"]
    assert agterm.raw()[0][-4:] == [
        "--socket",
        env["AGTERM_SOCKET"],
        "--window",
        env["AGTERM_WINDOW_ID"],
    ]


@pytest.mark.parametrize(
    ("name", "word", "mark"),
    [
        ("ask.no-status.html", None, None),
        ("ask.html", "no-status", None),
        ("ask.no-status.html", "status", MARK),
        (
            "ask.no-status.html",
            '["blocked", "--blink"]',
            [*MARK[:3], "--blink", *MARK[3:]],
        ),
    ],
    ids=("quiet-open", "quiet-wait", "marked-wait", "custom-mark"),
)
def test_the_latest_status_choice_holds(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    word: str | None,
    mark: list[str] | None,
) -> None:
    agterm, env = setup(tmp_path, name)
    if word is not None:
        (tmp_path / "lem-ask" / WAIT_WORD).write_text(word)
    monkeypatch.setattr(stop_agterm.time, "sleep", lambda _delay: None)
    monkeypatch.setattr(stop_agterm, "gettempdir", lambda: str(tmp_path))
    assert stop.answer(env, None) == ""
    marks = [call for call in agterm.calls() if call[:2] == ["session", "status"]]
    assert marks == ([mark] if mark else [])


def test_stop_leaves_the_mark_alone_after_the_board_answers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    agterm, env = setup(tmp_path)
    checkout = tmp_path / "repo"
    task = workspace(checkout)
    env.update(CLAUDE_PROJECT_DIR=str(checkout), LEM_TASK=task.name)
    (task / "task.json").write_text(
        json.dumps(
            {
                "task": {
                    "questions": [{"id": f"card:{PAGE}", "answer": {"source": "board"}}]
                }
            }
        )
    )
    monkeypatch.setattr(stop_agterm.time, "sleep", lambda _delay: None)
    monkeypatch.setattr(stop_agterm, "gettempdir", lambda: str(tmp_path))
    assert stop.answer(env, None) == ""
    assert agterm.calls() == [["tree", "--json"], ["tree", "--json"]]


def test_stop_is_silent_when_the_socket_does_not_answer(tmp_path: Path) -> None:
    agterm, env = setup(tmp_path)
    agterm.change(fail="tree")
    ran = hooked("stop", b"", **env)
    assert (ran.returncode, ran.stdout, ran.stderr) == (0, b"", b"")
    assert agterm.calls() == [["tree", "--json"]]


def test_stop_is_silent_when_the_status_call_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    agterm, env = setup(tmp_path)
    agterm.change(stop_after_second_tree=True)
    monkeypatch.setattr(stop_agterm.time, "sleep", lambda _delay: None)
    monkeypatch.setattr(stop_agterm, "gettempdir", lambda: str(tmp_path))
    assert stop.answer(env, None) == ""
    assert capsys.readouterr() == ("", "")
    assert agterm.calls() == [["tree", "--json"], ["tree", "--json"]]


def test_a_stalled_agterm_command_cannot_hold_the_hook(tmp_path: Path) -> None:
    agterm, env = setup(tmp_path)
    agterm.change(stall="tree")
    ran = subprocess.run(
        ["/bin/sh", "-c", LINES["stop"]],
        capture_output=True,
        env=claude_environ(env),
        input=b"",
        timeout=5,
        check=False,
    )
    assert (ran.returncode, ran.stdout, ran.stderr) == (0, b"", b"")
    pid = int((agterm.folder / "stalled.pid").read_text())
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)
