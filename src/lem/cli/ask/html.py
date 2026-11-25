"""A complete question page with its attachments and installed runtime."""

import json
from html import escape
from typing import TYPE_CHECKING

from lem.cli.ask import attachments, library
from lem.cli.ask.spec import check
from lem.kernel import paths

if TYPE_CHECKING:
    from pathlib import Path

    from lem.cli.ask.spec import Spec

TITLE_CHARS = 120  # the HTML head's title, as on main


def build(spec: Spec, base: Path) -> bytes:
    """Build the same page for a file, an overlay and the board."""
    check(spec)
    attachments.attach(spec, base)
    return frame(spec).encode("utf-8")


def frame(spec: Spec) -> str:
    """The document, with the spec in a JSON script that cannot open a tag."""
    root = paths.root()
    runtime = root / "skills" / "lem-ask" / "runtime"
    css = (runtime / "ask.css").read_text(encoding="utf-8")
    script = (runtime / "ask.js").read_text(encoding="utf-8")
    charts = library.script_of(root) if library.has_charts(spec) else ""
    return (
        '<!doctype html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{title_of(spec)}</title><style>{css}</style></head>"
        '<body><div id="app"></div><script type="application/json" id="hd-spec">'
        f"{script_json(spec)}</script>{charts}<script>{script}</script></body></html>"
    )


def script_json(spec: Spec) -> str:
    """Escape the tag opener wherever the spec has one."""
    return json.dumps(spec, ensure_ascii=False, allow_nan=False).replace("<", r"\u003c")


def title_of(spec: Spec) -> str:
    """The page title, or the first question when the page has no title."""
    questions = spec.get("questions")
    first = questions[0] if isinstance(questions, list) and questions else spec
    title = spec.get("title") or first.get("prompt") or "Question"
    return escape(str(title)[:TITLE_CHARS])
