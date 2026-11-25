"""The tab Artifacts of the refund line: its map with the line of each empty section, the file
the address names or else its first markdown document, each kind of file shown its way, and a
path that is no file of the task."""

from dataclasses import replace as changed
from typing import TYPE_CHECKING

import msgspec

from fixtures.board.moments import BASE
from fixtures.board.receipt import SLUG
from lem.board.inputs.parts import Link
from lem.board.views import owed
from lem.board.views.artifacts.chosen import missing
from lem.board.views.artifacts.tab import artifacts
from unit.board.views.afternoon import world

if TYPE_CHECKING:
    from pathlib import Path

    from lem.board.views.world import World

TAB = f"{BASE}/tasks/{SLUG}/artifacts"


def opened(found: World, path: str | None) -> World:
    """The afternoon with the tab Artifacts of the refund line open on `path`."""
    viewer = msgspec.structs.replace(
        found.viewer, task=SLUG, tab="artifacts", path=path
    )
    return changed(found, viewer=viewer)


def test_the_tab_shows_the_map_and_the_first_markdown_document(tmp_path: Path) -> None:
    found = world(tmp_path)
    tab = artifacts(found, owed.seen(found, SLUG))
    assert tab.said == "7 documents, read 16:00"
    empty = {section.key: section.empty for section in tab.sections}
    assert empty == {
        "request": None,
        "criteria": "no document: Criteria and decisions shows them",
        "plan": "not yet: the lead writes it",
        "build": None,
        "checks": None,
        "review": "no document: Checks and review shows each round",
        "pr": None,
    }
    report = tab.sections[3].docs[0]
    assert (report.title, report.icon, report.href) == (
        "Report",
        "file-lines",
        f"{TAB}/report.md/",
    )
    assert report.attached == (
        Link(
            href=f"{TAB}/media/receipt-after.png/",
            label="receipt-after.png",
            title="media/receipt-after.png",
            frame=True,
        ),
    )
    assert tab.shown and tab.shown.path == "task.md"
    assert tab.shown.meta == "task.md · markdown"
    document = tab.shown.body.document
    assert document and document.text.startswith("# refund-line-on-receipt")
    assert document.media == f"{BASE}/tasks/{SLUG}/media/"
    assert tab.sections[0].docs[0].selected
    assert not tab.chosen
    assert [folder.name for folder in tab.work] == [None, "Pictures"]
    assert tab.work_count == 3


def test_a_page_takes_the_whole_width_in_a_frame(tmp_path: Path) -> None:
    found = opened(world(tmp_path), "page.html")
    tab = artifacts(found, owed.seen(found, SLUG))
    assert tab.chosen and tab.wide
    raw = f"{BASE}/tasks/{SLUG}/raw/page.html"
    assert tab.shown and (tab.shown.alone, tab.shown.body.frame) == (raw, raw)


def test_a_picture_shows_from_the_media_folder_and_opens_its_folder(
    tmp_path: Path,
) -> None:
    found = opened(world(tmp_path), "media/receipt-before.png")
    tab = artifacts(found, owed.seen(found, SLUG))
    assert tab.shown and tab.shown.body.picture
    assert tab.shown.body.picture.src == f"{BASE}/tasks/{SLUG}/media/receipt-before.png"
    pictures = tab.work[1]
    assert pictures.open and pictures.docs[0].selected


def test_a_log_shows_its_lines_without_colors_and_a_file_not_read_says_so(
    tmp_path: Path,
) -> None:
    found = opened(world(tmp_path), "gate/01.log")
    seen = owed.seen(found, SLUG)
    tab = artifacts(found, seen)
    assert tab.shown and tab.shown.body.lines == (
        "....................",
        "214 passed in 3.1s",
    )
    assert tab.shown.icon == "terminal"
    unread = artifacts(found, msgspec.structs.replace(seen, prose=()))
    assert unread.shown and unread.shown.body.said == (
        "The board has no text of this file."
    )
    assert unread.shown.body.where == "It is at gate/01.log in the task’s folder."


def test_a_path_that_is_no_file_of_the_task_is_not_shown(tmp_path: Path) -> None:
    """The ruling "A task's artifacts have one map" (`main`'s
    test_board_task.Artifacts.test_one_file_is_read_only_by_a_path_the_task_lists): a file is
    shown only by a path the map lists."""
    found = opened(world(tmp_path), "../../task.json")
    seen = owed.seen(found, SLUG)
    assert missing(found, seen) == (
        "The task Refund line on receipt has no file '../../task.json'."
    )
    tab = artifacts(found, seen)
    assert not tab.chosen
    assert tab.shown and tab.shown.path == "task.md"
