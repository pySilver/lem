"""Read the UTF-8 JSON of a question and check what its page can show."""

import sys
from pathlib import Path

from lem.cli.ask import spec_types as shape
from lem.cli.ask import utf8
from lem.cli.ask.spec_question import FIELDS, own, questions
from lem.kernel.errors import Refusal

type Spec = dict[str, object]
type Loaded = tuple[Spec, Path]

MAX_PERCENT = 100


def parse(raw: str) -> Spec:
    """One spec as an object, with half characters made whole for UTF-8."""
    try:
        given = utf8.decode(raw)
    except (ValueError, RecursionError) as error:
        raise invalid(f"the question spec is no readable JSON: {error}") from error
    if not isinstance(given, dict):
        raise invalid("the question spec must be a JSON object")
    return given


def invalid(why: str) -> Refusal:
    """The refusal of a question page that cannot be built."""
    return Refusal(
        "ask-spec", why, "correct the spec using a template from lem ask templates"
    )


def load(named: str | None) -> Loaded:
    """Read a spec file or stdin, and give the base for its attachments."""
    path = Path(named).expanduser() if named and named != "-" else None
    try:
        raw = read_text(path)
    except (OSError, UnicodeError) as error:
        raise invalid(f"the question spec could not be read: {error}") from error
    base = path.resolve().parent if path else Path.cwd()
    return parse(raw), base


def read_text(path: Path | None) -> str:
    """The spec from a pipe, or a refusal instead of a terminal read."""
    if path is not None:
        return path.read_text(encoding="utf-8")
    if sys.stdin.isatty():
        raise invalid("the question has no spec file or JSON on stdin")
    return sys.stdin.buffer.read().decode("utf-8")


def check(spec: Spec) -> None:
    """Check the page and each question before it reaches the owner."""
    multi = "questions" in spec
    wires = own(spec)
    try:
        check_page(wires, multi=multi)
    except ValueError as error:
        raise invalid(str(error)) from error


def check_page(wires: Spec, *, multi: bool) -> None:
    """Check the page fields and the ids of each question."""
    top = wires
    if not multi:
        names = FIELDS & wires.keys()
        top = {key: wires[key] for key in names}
    page = shape.converted(top, shape.Page)
    if not size_ok(page.size):
        raise ValueError("size needs auto, full, or a percent from 1 to 100")
    questions(page, wires, multi=multi)


def size_ok(pct: object) -> bool:
    """The sizes a question accepts."""
    if isinstance(pct, int):
        return not isinstance(pct, bool) and 1 <= pct <= MAX_PERCENT
    return pct in ("auto", "full")
