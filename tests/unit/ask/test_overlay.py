"""The CLI's overlay outcomes with agterm's responses stood in."""

import json
import sys
from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from fakes import records
from lem.adapters import agterm_ctl
from lem.cli import lazy
from lem.cli.ask import answer, asking, html, quick, temp_pages
from lem.kernel import paths
from lem.records.holds import Parked
from lem.store import tasks
from unit.ask.conftest import PAGE, SLUG

if TYPE_CHECKING:
    from pathlib import Path
    from subprocess import CompletedProcess

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
    assert "--target" in request
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
    record = tasks.read(board.state, SLUG)
    assert [row.act for row in record.journal if hasattr(row, "act")] == [
        "card.asked",
        "card.closed",
    ]


@pytest.mark.parametrize("stopped", ["parked", "dropped"])
@pytest.mark.parametrize("ended", ["closed", "dismissed"])
def test_stopped_task_refuses_new_picks_but_can_retire_its_card(
    board: Board,
    terminal: Agterm,
    capsys: pytest.CaptureFixture[str],
    stopped: str,
    ended: str,
) -> None:
    from unit.ask.test_card import ORIGIN, ROUTE, posted, show

    show(terminal, capsys)
    record = tasks.read(board.state, SLUG)
    task = (
        replace(
            record.task, hold=Parked(since=records.MOMENT, words="The owner parks it")
        )
        if stopped == "parked"
        else replace(record.task, status="dropped")
    )
    tasks.update(
        board.state,
        SLUG,
        lambda current: replace(current, task=task),
        expect=record.revision,
    )
    digest = record.task.questions[0].digest
    assert digest
    with board.main() as client:
        refused = client.post(ROUTE + "/answer", json=posted(digest), headers=ORIGIN)
        assert refused.status_code == 409
    terminal.outcome = "submitted"
    terminal.payload = '"Keep"'
    late = result(capsys, ["wait", PAGE, "--no-status"])
    why = (
        f"card:{PAGE} no longer waits for the owner"
        if stopped == "parked"
        else f"{SLUG} is dropped: an ended task stays ended"
    )
    assert late == {"outcome": "refused", "pageID": PAGE, "said": why}
    terminal.outcome = None if ended == "closed" else "dismissed"
    words = ["close", PAGE] if ended == "closed" else ["wait", PAGE, "--no-status"]
    assert result(capsys, words)["outcome"] == ended
    if ended == "closed":
        assert terminal.shown is None
    assert result(capsys, ["wait", PAGE, "--no-status"])["outcome"] == ended
    after = tasks.read(board.state, SLUG)
    assert [row.act for row in after.journal if hasattr(row, "act")] == [
        "card.asked",
        "card.closed",
    ]
    assert after.task.status == task.status
    assert after.task.hold == task.hold


def test_permanent_page_refusal_ends_the_wait_on_the_first_read(
    terminal: Agterm,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    terminal.error = "no such page"
    monkeypatch.setattr("lem.cli.ask.waiting.POLL", 0)
    refused = result(capsys, ["wait", PAGE, "--no-status", "--timeout", "1"])
    assert refused["outcome"] == "unavailable"
    assert "no such page" in refused["said"]
    assert len(terminal.calls) == 1


def test_pending_reads_do_not_use_up_the_unreadable_reply_limit(
    terminal: Agterm,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pending_reads = 6

    def becomes_ready(env: dict, *words: str, **flags: object) -> CompletedProcess[str]:
        if len(terminal.calls) == pending_reads:
            terminal.outcome = "submitted"
            terminal.payload = '"Keep"'
        return terminal.ctl(env, *words, **flags)

    monkeypatch.setattr(agterm_ctl, "ctl", becomes_ready)
    monkeypatch.setattr("lem.cli.ask.waiting.POLL", 0)
    picked = result(capsys, ["wait", PAGE, "--no-status", "--timeout", "1"])
    assert picked["outcome"] == "answered"
    assert picked["answers"]["answer"]["text"] == "Keep"
    assert len(terminal.calls) == pending_reads + 1


@pytest.mark.parametrize("no_wait", [False, True])
def test_overlay_survives_a_board_copy_that_cannot_be_saved(
    board: Board,
    terminal: Agterm,
    capsys: pytest.CaptureFixture[str],
    *,
    no_wait: bool,
) -> None:
    (board.state / "tasks" / SLUG / "cards").write_text("This is a file.")
    terminal.outcome = "submitted"
    terminal.payload = '"Keep"'
    words = ["q", "Keep it?", "--no-status"]
    if no_wait:
        words.append("--no-wait")
    assert lazy.main(["ask", *words]) == 0
    captured = capsys.readouterr()
    printed = json.loads(captured.out)["result"]
    assert printed["outcome"] == ("open" if no_wait else "answered")
    assert printed["pageID"] == PAGE
    assert terminal.shown is not None
    assert f"the board does not show card {PAGE}" in captured.err
    assert tasks.read(board.state, SLUG).task.questions == ()


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


def test_unreadable_overlay_json_returns_the_original_text(
    terminal: Agterm,
    capsys: pytest.CaptureFixture[str],
) -> None:
    digits = "9" * (sys.get_int_max_str_digits() + 1)
    nested = "[" * 100_000 + "]" * 100_000
    depth = sys.getrecursionlimit()
    deep_object = '{"a":' * depth + "1" + "}" * depth
    for raw in (digits, '{"n":' + digits + "}", nested, deep_object):
        terminal.outcome = "submitted"
        terminal.payload = raw
        picked = result(capsys, ["wait", PAGE, "--no-status"])
        assert picked["pageID"] == PAGE
        assert picked["answers"]["answer"] == {
            "selected": [],
            "labels": [],
            "text": raw,
        }


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


def test_skill_names_the_cli_outcomes_and_resume_command() -> None:
    skill = paths.root() / "skills" / "lem-ask" / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    for fragment in (
        "result.outcome",
        "`pending`",
        "`lem ask wait PAGEID`",
        "`lem ask close PAGEID`",
        "`lem ask templates`",
    ):
        assert fragment in text


def test_harness_names_the_cli_outcomes_and_resume_command() -> None:
    harness = (
        paths.root() / "skills" / "lem" / "harness" / "claude-code" / "ask-owner.md"
    )
    text = harness.read_text(encoding="utf-8")
    for fragment in (
        '`result.outcome: "pending"`',
        "`lem ask wait PAGEID`",
        "`lem ask close`",
    ):
        assert fragment in text


@pytest.mark.parametrize("browser", [False, True])
def test_ask_checks_the_spec_once_before_dispatch(
    terminal: Agterm,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    *,
    browser: bool,
) -> None:
    check = html.check
    checked = []

    def count(spec: dict[str, object]) -> None:
        checked.append(spec)
        check(spec)

    monkeypatch.setattr(asking, "check", count)
    monkeypatch.setattr(html, "check", count)
    monkeypatch.setattr(
        "lem.cli.ask.browser.ask", lambda _page, _timeout: {"outcome": "answered"}
    )
    words = ["--browser"] if browser else ["--no-wait"]
    assert result(capsys, ["q", "What should the owner do?", *words])["outcome"] == (
        "answered" if browser else "open"
    )
    assert len(checked) == 1
