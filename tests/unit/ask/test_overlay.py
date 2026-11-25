"""The CLI's overlay outcomes with agterm's responses stood in."""

import json
from typing import TYPE_CHECKING

import pytest

from lem.cli import lazy
from lem.cli.ask import answer, quick, temp_pages
from unit.ask.conftest import PAGE

if TYPE_CHECKING:
    from pathlib import Path

    from unit.ask.conftest import Agterm
    from unit.board.service.given import Board


def result(capsys: pytest.CaptureFixture[str], words: list[str]) -> dict:
    assert lazy.main(["ask", *words]) == 0
    return json.loads(capsys.readouterr().out)["result"]


def test_q_opens_without_focus_then_busy_names_only_our_question(
    terminal: Agterm, capsys: pytest.CaptureFixture[str]
) -> None:
    shown = result(
        capsys, ["q", "Stay?", "*Stay|Keep the value|The export needs it", "--no-wait"]
    )
    assert shown["outcome"] == "open"
    assert shown["pageID"] == PAGE
    request = terminal.calls[0]
    assert "--follow" not in request
    assert "--html" in request
    assert result(capsys, ["q", "Another?", "--no-wait"])["pageID"] == PAGE
    terminal.shown = "/elsewhere/review.html"
    busy = result(capsys, ["q", "Another?", "--no-wait"])
    assert busy["outcome"] == "busy"
    assert "pageID" not in busy
    assert result(capsys, ["close"])["outcome"] == "gone"
    assert all("close" not in call for call in terminal.calls)


def test_wait_timeout_can_resume_and_last_wait_controls_the_stop_word(
    terminal: Agterm, capsys: pytest.CaptureFixture[str]
) -> None:
    result(capsys, ["q", "Coffee?", "--no-wait", "--no-status"])
    word = temp_pages.folder() / f"{PAGE}.wait.html"
    assert word.read_text() == "no-status"
    assert result(capsys, ["wait", PAGE, "--timeout", "0"])["outcome"] == "pending"
    assert word.read_text() == "status"
    terminal.outcome = "submitted"
    terminal.payload = "[1]"
    picked = result(capsys, ["wait", PAGE, "--no-status", "--timeout", "0"])
    assert picked["outcome"] == "answered"
    assert picked["answers"]["answer"]["text"] == "[1]"
    assert word.read_text() == "no-status"


def test_close_keeps_an_end_for_the_waiter(
    board: Board, terminal: Agterm, capsys: pytest.CaptureFixture[str]
) -> None:
    result(capsys, ["q", "Keep the cell?", "--no-wait"])
    assert result(capsys, ["close", "P9"])["outcome"] == "gone"
    assert terminal.shown is not None
    assert result(capsys, ["close", PAGE])["outcome"] == "closed"
    assert terminal.shown is None
    assert result(capsys, ["wait", PAGE, "--no-status"])["outcome"] == "closed"


def test_dismissed_and_unavailable_are_outcomes(
    terminal: Agterm,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    terminal.outcome = "dismissed"
    assert (
        result(capsys, ["wait", PAGE, "--no-status", "--timeout", "0"])["outcome"]
        == "dismissed"
    )
    terminal.silent = True
    monkeypatch.setattr("lem.cli.ask.waiting.POLL", 0)
    assert (
        result(capsys, ["wait", PAGE, "--no-status", "--timeout", "1"])["outcome"]
        == "unavailable"
    )


def test_no_agterm_and_unattended_are_exit_zero(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    assert result(capsys, ["q", "Stay?"])["outcome"] == "no-agterm"
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ATTENDED", "0")
    assert result(capsys, ["q", "Stay?"])["outcome"] == "unattended"


@pytest.mark.parametrize(
    ("wire", "expected"),
    [
        ('"hello"', "hello"),
        ("null", "null"),
        ("42", "42"),
        ("true", "true"),
        ("words", "words"),
        (r'"\ud800"', "\ufffd"),
    ],
)
def test_script_values_can_be_one_text_answer(wire: str, expected: str) -> None:
    picked = json.loads(json.dumps(answer.submitted(wire)))
    assert picked["answers"]["answer"]["text"] == expected


def test_short_option_keeps_the_reason_and_normalizes_half_characters() -> None:
    marked = quick.option("*Do it\ud800|small change|current tool", 1)
    assert marked == {
        "id": "o1",
        "label": "Do it\ufffd",
        "subtitle": "small change",
        "recommended": "current tool",
    }


def test_spec_default_verb_and_named_demo_open_their_pages(
    terminal: Agterm, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    named = tmp_path / "card.json"
    named.write_text('{"prompt":"Keep it?", "options":["Keep","Write a dash"]}')
    for words in (["ask", str(named)], [str(named)], ["demo", "pick"]):
        assert result(capsys, [*words, "--no-wait"])["outcome"] == "open"
        assert result(capsys, ["close"])["outcome"] == "closed"
    assert terminal.shown is None
