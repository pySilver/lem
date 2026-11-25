"""Compare the typed showcase to semantic HTML facts taken from main's saved pages."""

import json
from pathlib import Path
from typing import TYPE_CHECKING

import msgspec
import pytest

from fixtures.board import columns, frame, panel, shelves, waiting
from lem.board.inputs.page import Page
from lem.board.pages.render import section
from unit.board.pages.markup import Parsed

if TYPE_CHECKING:
    from lem.board.inputs.page import Frame
    from lem.board.inputs.text import View

if TYPE_CHECKING:
    from unit.board.pages.markup import Node

BASELINE = Path(__file__).with_name("main-showcase.json")
REFUND = "task-refund-line-on-receipt-"


def for_view(view: View, title: str) -> Frame:
    """Put the fixture's shared frame over a different view."""
    template = frame.FRAME
    changed = msgspec.structs.replace
    rows = tuple(
        changed(hit, href=f"{hit.href}?in={view}") if hit.kind == "task" else hit
        for hit in template.search.rows
    )
    return changed(
        template,
        viewer=changed(template.viewer, view=view),
        head=changed(
            template.head,
            title=template.head.title.replace("· Tasks ·", f"· {title} ·"),
        ),
        topbar=changed(template.topbar, title=title),
        search=changed(template.search, rows=rows),
    )


SAMPLES = (
    ("kanban_page", Page(frame=frame.FRAME, tasks=columns.TASKS)),
    ("waits_page", Page(frame=for_view("waits", "Waits for you"), waits=waiting.WAITS)),
    (
        "backlog_page",
        Page(frame=for_view("backlog", "Backlog"), backlog=shelves.BACKLOG),
    ),
    (REFUND + "overview", Page(frame=frame.FRAME, panel=panel.OPEN)),
    (REFUND + "criteria", Page(frame=frame.FRAME, panel=panel.CRITERIA_TAB)),
    (REFUND + "checks", Page(frame=frame.FRAME, panel=panel.CHECKS_TAB)),
    (REFUND + "merge", Page(frame=frame.FRAME, panel=panel.MERGE_STEP)),
)


def names(parts: list[Node]) -> list[str | None]:
    return [part.attrs["id"] for part in parts]


def links(parts: list[Node]) -> list[tuple[str, str | None]]:
    return [(part.words(), part.attrs["href"]) for part in parts]


def documents(tree: Node) -> list[tuple[str | None, str]]:
    return [
        (part.attrs["id"], part.one(tag="template").raw())
        for part in tree.all(cls="md")
        if part.all(tag="template")
    ]


def shell(tree: Node) -> dict[str, object]:
    return {
        "title": tree.one(tag="head").one(tag="title").words(),
        "views": [view.attrs["href"] for view in tree.all(cls="vbtn")],
        "search": [
            (hit.attrs["id"], hit.attrs["href"], hit.attrs.get("data-title"))
            for hit in tree.all(cls="sr")
        ],
        "columns": names(tree.all(cls="col")),
        "card links": links(tree.all(cls="tc-link")),
        "stack IDs": names(tree.all(cls="wstack")),
        "wait IDs": names(tree.all(cls="wrow", tag="article")),
        "parked": names(
            [
                part
                for part in tree.all(cls="bl-item")
                if (part.attrs["id"] or "").startswith("parked-")
            ]
        ),
        "backlog": names(tree.all(cls="bl-group")),
        "items": names(
            [
                part
                for part in tree.all(cls="bl-item")
                if (part.attrs["id"] or "").startswith("item-")
            ]
        ),
    }


def task(tree: Node) -> dict[str, object]:
    return {
        "panel task": tree.one(id_="panel").attrs["data-task"],
        "title": tree.one(cls="p-title").words(),
        "tabs": [(tab.attrs["id"], tab.attrs["href"]) for tab in tree.all(cls="ptab")],
        "active tab": [
            tab.attrs["id"]
            for tab in tree.all(cls="ptab")
            if "aria-current" in tab.attrs
        ],
        "documents": documents(tree),
        "decisions": names(
            [
                row
                for row in tree.all(cls="dec", tag="details")
                if (row.attrs["id"] or "").startswith("dec-")
            ]
        ),
        "forge links": sorted(
            {
                node.attrs["href"] or ""
                for node in tree.all(tag="a")
                if (node.attrs.get("href") or "").startswith(
                    "https://github.com/acme/shop/pull/"
                )
            }
        ),
    }


@pytest.mark.parametrize(
    ("sample", "board"), SAMPLES, ids=[name for name, _ in SAMPLES]
)
def test_showcase_matches_main_on_the_saved_section(sample: str, board: Page) -> None:
    fragment = board.panel is not None
    template = "fragment.html" if fragment else "page.html"
    observed = task if fragment else shell
    tree = Parsed(section(template, board)).root
    expected = json.loads(BASELINE.read_text(encoding="utf-8"))
    assert json.loads(json.dumps(observed(tree))) == expected[sample]


def test_jinja_preserves_the_native_whole_visit() -> None:
    viewer = msgspec.structs.replace(frame.FRAME.viewer, native=True)
    board = Page(
        frame=msgspec.structs.replace(frame.FRAME, viewer=viewer), tasks=columns.TASKS
    )
    tree = Parsed(section("page.html", board)).root
    assert "data-turbo-frame" not in tree.all(cls="tc-link")[0].attrs
    assert tree.one(id_="stage").has("native")
