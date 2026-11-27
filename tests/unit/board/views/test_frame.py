"""The frame of the afternoon's page Tasks, from its records: the head, the phone's bar, the
sidebar with what waits for the owner, the bars, and the search over every card of
`fixtures.board.frame`."""

from dataclasses import replace
from typing import TYPE_CHECKING

import msgspec
import pytest

from fixtures.board import frame
from fixtures.board.moments import HOST, WORKSPACE
from lem.board.inputs.switcher import Switcher
from lem.board.views.frame.page import Beside
from lem.board.views.frame.page import frame as framed
from unit.board.views.afternoon import world

if TYPE_CHECKING:
    from pathlib import Path


def test_the_frame_of_the_afternoons_page_tasks_is_todays(tmp_path: Path) -> None:
    seen = world(tmp_path)
    made = framed(seen, Beside(backlog=1))
    assert made.head == frame.FRAME.head
    assert made.phonebar == frame.FRAME.phonebar
    assert made.topbar == frame.FRAME.topbar
    assert made.statusbar == frame.FRAME.statusbar
    assert made.keys == frame.FRAME.keys
    for one, other in zip(made.sidebar.waits, frame.SIDEBAR.waits, strict=True):
        assert one == other, one.id
    assert made.sidebar == frame.SIDEBAR
    task_rows = tuple(row for row in frame.SEARCH.rows if row.kind == "task")
    assert made.search.rows == task_rows


@pytest.mark.parametrize("joined", (False, True))
@pytest.mark.parametrize("task", (None, "refund-line-on-receipt"))
def test_the_tab_title_names_the_machine_only_on_a_joined_board(
    tmp_path: Path, *, joined: bool, task: str | None
) -> None:
    seen = world(tmp_path)
    seen = replace(seen, viewer=msgspec.structs.replace(seen.viewer, task=task))
    switcher = Switcher(
        name=WORKSPACE, title="Workspaces", host=HOST if joined else None
    )
    made = framed(seen, Beside(switcher=switcher))
    where = f"{HOST}/{WORKSPACE}" if joined else WORKSPACE
    if task:
        assert made.head.title.startswith("DEMO · Refund line on receipt · ")
        assert made.head.title.endswith(f" · Lem · {where}")
    else:
        assert made.head.title == f"DEMO · Tasks · Lem · {where} · 2 build · 5 for you"
