"""The board's inline Markdown, clock seconds and static icon symbols."""

import hashlib
import json
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

import msgspec
from markdown_it import MarkdownIt

from lem.kernel import paths

if TYPE_CHECKING:
    from datetime import datetime

INLINE = MarkdownIt("commonmark").disable("html_inline")


def inline(words: str) -> str:
    """Render a line of Markdown with raw HTML escaped."""
    return INLINE.renderInline(words)


def milliseconds(at: datetime) -> int:
    """The browser's clock reads Unix milliseconds."""
    return int(at.timestamp() * 1000)


def icons() -> dict[str, dict[str, str]]:
    """The symbols of the kit, whose SVG paths come from the installed assets."""
    vendor = paths.root() / "skills" / "lem" / "assets" / "vendor"
    return json.loads((vendor / "board-icons.json").read_text(encoding="utf-8"))


def read_key(part: msgspec.Struct) -> str:
    """The sheet's read applies only to the step and facts shown."""
    return hashlib.sha256(msgspec.json.encode(part)).hexdigest()


def address(href: str) -> str:
    """Allow a board-relative address or a normal external link."""
    scheme = urlsplit(href).scheme
    if scheme in {"http", "https", "mailto", "tel"}:
        return href
    if (
        not scheme
        and "\\" not in href
        and href.startswith(("/", "#"))
        and not href.startswith("//")
    ):
        return href
    raise ValueError("Give the board a relative address or an HTTP link.")
