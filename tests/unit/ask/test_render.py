"""The shipped questions and the spec and attachments they take."""

import json
import re
from typing import TYPE_CHECKING

import pytest

from lem.cli import lazy
from lem.cli.ask import catalog, html, spec
from lem.kernel import paths
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from pathlib import Path

ROOT = paths.root() / "skills" / "lem-ask"


def test_every_template_and_demo_renders_without_a_download(tmp_path: Path) -> None:
    for example in catalog.examples():
        named = ROOT / example["folder"] / f"{example['name']}.json"
        asked, base = spec.load(str(named))
        page = html.build(asked, base)
        assert b'id="hd-spec"' in page
        assert b"session.overlay.submit" in page
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(
    "body",
    [
        "[]",
        '{"questions": ["x"]}',
        '{"prompt": "Which?", "options": [1]}',
        '{"prompt": "Which?", "options": ["A", "A"]}',
        '{"questions": [{"id": "a", "prompt": "A"}, {"id": "a", "prompt": "B"}]}',
        '{"prompt": "Which?", "options": ["Option A"]}',
        '{"prompt": "Which?", "controls": ["x"]}',
        '{"prompt": "Which?", "size": 101}',
        '{"prompt": "Which?", "subtitel": "try this"}',
        '{"prompt": "Which?", "options": [{"label": null}]}',
        '{"prompt": "Which?", "options": [{"label": "A", "detailz": "x"}]}',
        '{"prompt": "Which?", "mode": "checkbox"}',
        '{"prompt": "Which?", "review": "often"}',
        '{"options": ["Yes"]}',
    ],
)
def test_invalid_specs_refuse_before_the_owner_sees_them(
    body: str, tmp_path: Path
) -> None:
    with pytest.raises(Refusal, match=r".+"):
        html.build(spec.parse(body), tmp_path)


def test_attachment_lines_and_images_stay_in_the_standalone_file(
    tmp_path: Path,
) -> None:
    (tmp_path / "code.py").write_text("one\ntwo\nthree\n")
    (tmp_path / "dot.png").write_bytes(b"little image")
    asked: spec.Spec = {
        "prompt": "Keep it?",
        "context": [
            {"code": {"file": "code.py", "lines": [2, 3]}},
            {"image": "dot.png"},
            {"md": "```mermaid\nflowchart LR\n A --> B\n```"},
        ],
    }
    page = html.build(asked, tmp_path).decode()
    blocks = page_spec(page)["context"]
    assert blocks[0] == {
        "code": "two\nthree",
        "start": 2,
        "title": "code.py:2-3",
        "lang": "py",
    }
    assert blocks[1]["image"] == "data:image/png;base64,bGl0dGxlIGltYWdl"
    assert "<script>" in page
    assert "window.pele.render" in page
    assert len(page) > 700_000


def test_strings_stay_utf8_and_cannot_close_the_spec_script(tmp_path: Path) -> None:
    asked = spec.parse(r'{"prompt":"A\ud800", "context":"</script><!--<script>"}')
    page = html.build(asked, tmp_path).decode()
    assert page_spec(page)["prompt"] == "A\ufffd"
    assert page_spec(page)["context"] == "</script><!--<script>"
    assert "</script><!--<script>" not in page


def test_render_and_catalog_emit_one_json_document(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    named = tmp_path / "question.json"
    named.write_text('{"prompt": "Keep a dash?"}')
    target = tmp_path / "question.html"
    assert lazy.main(["ask", "render", str(named), "--out", str(target)]) == 0
    r = json.loads(capsys.readouterr().out)["result"]
    assert r == {"outcome": "rendered", "file": str(target)}
    assert page_spec(target.read_text())["style"] == "refined"
    assert lazy.main(["ask", "templates"]) == 0
    assert json.loads(capsys.readouterr().out)["result"]["templates"]
    assert lazy.main(["ask", "demo"]) == 0
    assert json.loads(capsys.readouterr().out)["result"]["demos"]


def page_spec(page: str) -> dict:
    found = re.search(r'id="hd-spec">(.*?)</script>', page, flags=re.DOTALL)
    assert found
    return json.loads(found[1])


def test_counted_option_with_explanation_passes_and_plain_page_has_no_chart_bundle(
    tmp_path: Path,
) -> None:
    asked = spec.parse(
        '{"prompt":"Which?","options":[{"label":"Option A","subtitle":"Write a dash"}]}'
    )
    page = html.build(asked, tmp_path)
    assert b"Write a dash" in page
    assert page.count(b"<script>") == 1


def test_unreadable_json_number_refuses_with_a_fix() -> None:
    with pytest.raises(Refusal, match="no readable JSON"):
        spec.parse('{"prompt":"A?","_large":' + "9" * 5500 + "}")


@pytest.mark.parametrize("key", ["mode", "layout", "columns"])
@pytest.mark.parametrize("multi", [False, True])
def test_null_question_fields_are_refused(
    tmp_path: Path, key: str, *, multi: bool
) -> None:
    question: spec.Spec = {"prompt": "Keep it?", key: None}
    given: spec.Spec = {"questions": [question]} if multi else question
    with pytest.raises(Refusal, match=key):
        html.build(given, tmp_path)
    assert html.build({"prompt": "Keep it?"}, tmp_path)


@pytest.mark.parametrize(
    ("given", "mistake", "suggestion"),
    [
        ({"prompt": "Keep it?", "subtitel": "Change"}, "subtitel", "subtitle"),
        ({"prompt": "Keep it?", "layuot": "list"}, "layuot", "layout"),
        (
            {"prompt": "Keep it?", "options": [{"label": "Yes", "detailz": "Change"}]},
            "detailz",
            "detail",
        ),
    ],
)
def test_misspelled_spec_keys_name_the_fix(
    tmp_path: Path, given: spec.Spec, mistake: str, suggestion: str
) -> None:
    with pytest.raises(Refusal, match=mistake) as refused:
        html.build(given, tmp_path)
    assert f"did you mean {suggestion!r}?" in refused.value.why


def test_missing_local_images_show_alt_text(
    tmp_path: Path,
) -> None:
    asked: spec.Spec = {
        "prompt": "Keep it?",
        "context": [
            {"image": "missing.png", "alt": "A preview of the export"},
            {"image": "other.png"},
        ],
    }
    page = html.build(asked, tmp_path).decode()
    assert page_spec(page)["context"] == [
        {"image": "", "alt": "A preview of the export"},
        {"image": "", "alt": "missing image: other.png"},
    ]


def test_render_refuses_bad_home_ask_settings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    cases = (
        ("[ask]\nbrowser = 2026-11-23", "ask.browser", "true or false"),
        ('[ask]\nstyle = "minmal"', "ask.style", '"minimal"'),
        ('[ask]\nreview = "sometimes"', "ask.review", '"never"'),
        ('[ask]\nsize = "big"', "ask.size", "percent"),
        ('[ask.status]\nasking = "blocked"', "ask.status", "asking"),
        ('[ask]\nstlye = "bold"', "ask.stlye", "did you mean style"),
        ("ask = 5", "ask", "correct"),
        ("[ask", "TOML", "correct"),
    )
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    settings = tmp_path / "lem" / "settings.toml"
    settings.parent.mkdir()
    named = tmp_path / "spec.json"
    named.write_text('{"prompt":"Keep it?"}')
    target = tmp_path / "card.html"
    for toml, why, fix in cases:
        settings.write_text(toml)
        assert lazy.main(["ask", "render", str(named), "--out", str(target)]) == 1
        refused = json.loads(capsys.readouterr().out)["refusal"]
        assert str(settings) in refused["why"]
        assert why in refused["why"]
        assert fix in refused["fix"]
        assert not target.exists()
