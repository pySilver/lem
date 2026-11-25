"""A text file of a task as the tab Artifacts shows it (`board_task.art_body` on `main`): a log as
its lines with no terminal colors, a JSON value indented, JSON lines one value a line, any other
text as it is; and the tab that shows a record readable."""

import json
import re
from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.board.inputs.names import task_href
from lem.board.inputs.parts import Link
from lem.board.inputs.task.artifacts import Body

if TYPE_CHECKING:
    from lem.board.inputs.task.artifacts import Kind
    from lem.board.views.artifacts.mapped import Entry
    from lem.board.views.world import World

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
# The tabs that show a record readable, by their key, as a record's line names them.
TABS = MappingProxyType(
    {
        "criteria": "Criteria and decisions",
        "checks": "Checks and review",
        "timeline": "Timeline",
    }
)
NOT_JSON = "This file is not valid JSON; it is shown as written."


def indented(text: str) -> str | None:
    """A JSON value indented by two, or None when the text is no JSON."""
    try:
        return json.dumps(json.loads(text), indent=2, ensure_ascii=False)
    except ValueError:
        return None


def one_line(line: str) -> str:
    """One line of JSON lines as one value, or as written when it is no JSON."""
    try:
        return json.dumps(json.loads(line), ensure_ascii=False)
    except ValueError:
        return line


def shown(kind: Kind, text: str, where: str, record: Link | None) -> Body:
    """The text file of kind `kind` as the tab shows it."""
    plain = ANSI.sub("", text)
    if kind == "log":
        lines = plain.rstrip("\n").split("\n")
        return Body(lines=tuple(lines), where=where)
    if kind == "jsonl":
        written = filter(str.strip, text.split("\n"))
        return Body(lines=tuple(map(one_line, written)), record=record, where=where)
    if kind == "json":
        pretty = indented(text)
        said = NOT_JSON if pretty is None else None
        return Body(text=pretty or text, said=said, record=record, where=where)
    return Body(text=plain, where=where)


def record_of(world: World, slug: str, entry: Entry) -> Link | None:
    """The tab that shows a record readable, or None."""
    tab = entry.spot.tab
    if entry.spot.role != "record" or tab is None or tab not in TABS:
        return None
    href = task_href(world.viewer.base, slug, tab, world.viewer.view)
    return Link(href=href, label=TABS[tab], frame=True)
