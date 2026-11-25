"""Shared card modules, answer modes, defaults, and the browser's outcome loop."""

from importlib.util import find_spec
from typing import TYPE_CHECKING, cast

import pytest

from lem.app.asking import form
from lem.app.asking.shape import Pick, Posted
from lem.board.ask import body, verify
from lem.cli.ask import browser, preferences
from lem.kernel.errors import Refusal
from lem.settings.shared import Ask

if TYPE_CHECKING:
    from pathlib import Path

    from lem.cli.ask.answer import Words
    from lem.cli.ask.browser_http import BrowserServer


def test_card_modules_live_in_the_shared_app_layer() -> None:
    assert find_spec("lem.app.asking") is not None
    for module in (
        "ends",
        "form",
        "keys",
        "overlay_read",
        "receipts",
        "saved",
        "shape",
        "updates",
    ):
        assert find_spec(f"lem.app.asking.{module}") is not None
        assert find_spec(f"lem.board.ask.{module}") is None


def test_tune_optional_text_and_multi_use_the_saved_form() -> None:
    card = form.metadata(
        {
            "questions": [
                {
                    "prompt": "How large?",
                    "controls": [{"id": "radius"}],
                    "options": ["Soft"],
                },
                {"prompt": "Any other change?", "mode": "multi", "optional": True},
                {"id": "words", "prompt": "Why?"},
                {
                    "id": "both",
                    "prompt": "What else?",
                    "mode": "multi",
                    "min": 2,
                    "options": ["A", "B"],
                },
            ]
        },
        "P1",
        "S1",
    )
    answers = {
        "q1": Pick(controls={"radius": 14}, preset="Soft"),
        "q2": Pick(),
        "words": Pick(text="The owner needs both"),
        "both": Pick(selected=("A", "B")),
    }
    posted = Posted(status="answered", answers=answers)
    checked = verify.normalized(card.prompts, posted)
    assert checked.answers["q1"].controls == {"radius": 14}
    assert checked.answers["q1"].preset == "Soft"
    assert checked.answers["q2"] == Pick()
    assert checked.answers["both"].labels == ("A", "B")
    for key, bad in (
        ("q1", Pick()),
        ("words", Pick(text=" ")),
        ("both", Pick(selected=("A",))),
    ):
        with pytest.raises(Refusal):
            verify.normalized(
                card.prompts, Posted(status="answered", answers={**answers, key: bad})
            )


def test_posted_note_keeps_half_a_character_as_utf8() -> None:
    picked = body.decode(
        bytearray(rb'{"status":"answered","answers":{"answer":{"text":"A\ud800"}}}')
    )
    assert picked is not None
    assert picked.answers["answer"].text == "A\ufffd"


def test_question_defaults_come_from_the_home_settings(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config = tmp_path / "lem"
    config.mkdir()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    (config / "settings.toml").write_text(
        '[ask]\nstyle = "minimal"\nreview = true\nsize = 83\n'
        'browser = true\n[ask.status]\nasking = ["blocked", "--sound", "default"]\n'
    )
    pref = preferences.defaults()
    assert isinstance(pref, Ask)
    assert (pref.style, pref.review, pref.size, pref.browser) == (
        "minimal",
        True,
        83,
        True,
    )
    assert pref.status["asking"] == ("blocked", "--sound", "default")


class BrowserStandIn:
    """The browser server loop with no listener."""

    timeout: float = 0
    answer: Words | None = None
    dismissed: float | None = None

    def handle_request(self) -> None:
        self.answer = {"status": "answered", "answers": {"answer": {"text": "[1]"}}}


def test_browser_wait_returns_the_posted_answer_in_the_command_envelope() -> None:
    result = browser.wait(cast("BrowserServer", BrowserStandIn()), float("inf"))
    assert result["outcome"] == "answered"
    assert result["answers"] == {"answer": {"text": "[1]"}}
