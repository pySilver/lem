"""The afternoon's pages whole, from its records: the frame of `fixtures.board.frame` with the
search over every card and the Backlog key's count, and under it the one view of the address."""

from dataclasses import replace
from typing import TYPE_CHECKING

import msgspec

from fixtures.board import columns, frame, shelves, waiting
from fixtures.board.shown import VIEWER
from lem.board.views import pages
from unit.board.views.afternoon import world

if TYPE_CHECKING:
    from pathlib import Path


def test_the_page_tasks_is_todays_frame_and_columns(tmp_path: Path) -> None:
    made = pages.page(world(tmp_path))
    assert made.frame.search == frame.SEARCH
    assert made.frame == frame.FRAME
    assert made.tasks == columns.TASKS
    assert (made.waits, made.backlog, made.panel) == (None, None, None)


def test_the_page_waits_for_you_has_its_view_and_keys(tmp_path: Path) -> None:
    viewer = msgspec.structs.replace(VIEWER, view="waits")
    made = pages.page(world(tmp_path, viewer))
    assert made.waits == waiting.WAITS
    assert made.frame.keys == waiting.KEYS
    assert made.frame.topbar.summary == "5 tasks wait for you, the most pressing first"
    assert made.tasks is None


def test_the_page_backlog_has_its_view_and_keys(tmp_path: Path) -> None:
    viewer = msgspec.structs.replace(VIEWER, view="backlog")
    made = pages.page(world(tmp_path, viewer))
    assert made.backlog == shelves.BACKLOG
    assert made.frame.keys == shelves.KEYS
    assert made.frame.sidebar.views[2].current


def test_with_no_backlog_read_the_key_counts_nothing_and_the_search_has_no_item(
    tmp_path: Path,
) -> None:
    made = pages.page(replace(world(tmp_path), backlog=None))
    assert made.frame.sidebar.views[2].count is None
    assert all(row.kind == "task" for row in made.frame.search.rows)
