"""The local text of a code, diff, markdown or chart block."""

from pathlib import Path
from typing import TYPE_CHECKING

from lem.cli.ask.spec import invalid

if TYPE_CHECKING:
    from lem.cli.ask.spec import Spec

CODE = "code"
PAIR = 2
KINDS = (CODE, "diff", "md", "mermaid")
CODE_LIMIT = 300  # the bound of a whole code block on main


def lines_of(selection: object, count: int) -> tuple[int, int]:
    """Read a one-based inclusive range from a number, a range or a pair."""
    if isinstance(selection, list) and len(selection) == PAIR:
        first, last = selection
    else:
        first, _, last = str(selection).partition("-")
        last = last or first
    try:
        start, stop = int(first), int(last)
    except TypeError, ValueError:
        raise invalid(f"lines need a range like 40-60, got {selection!r}") from None
    in_file = 1 <= start <= count
    if not in_file or not start <= stop <= count:
        raise invalid(f"lines {start}-{stop} are outside the file's 1-{count}")
    return start, stop


def fill(block: Spec, kind: str, ref: Spec, base: Path) -> None:
    """Put the file's text and its line numbers into a block."""
    named = ref["file"]
    if not isinstance(named, str) or not named.strip():
        raise invalid(f"the {kind} block needs its file path in quotes")
    path = Path(base, Path(named).expanduser())
    words = text_of(path)
    block[kind] = cropped(block, kind, ref, words)
    if kind == CODE:
        block.setdefault("title", named)
        if path.suffix:
            block.setdefault("lang", path.suffix.removeprefix("."))


def cropped(block: Spec, kind: str, ref: Spec, words: str) -> str:
    """The requested lines, or the whole file when it fits the code page."""
    lines = words.splitlines()
    if "lines" in ref:
        selection = ref.get("lines")
        first, last = lines_of(selection, len(lines))
        if kind == CODE:
            block.setdefault("start", first)
        return "\n".join(lines[first - 1 : last])
    if kind == CODE and len(lines) > CODE_LIMIT:
        raise invalid(f"the code block exceeds {CODE_LIMIT} lines; give a line range")
    return words


def text_of(path: Path) -> str:
    """Refuse a text attachment that cannot be read."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise invalid(f"the attachment {path} could not be read: {error}") from error
