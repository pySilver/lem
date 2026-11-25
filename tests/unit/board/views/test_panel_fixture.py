"""The panel of the refund line as the board draws it on the showcase afternoon (`main`'s
`board_task.panel`, `overview_tab` and `merge_step`)."""

from typing import TYPE_CHECKING

from fixtures.board import panel as expected
from fixtures.board.receipt import SLUG
from lem.board.views.panel.panel import panel
from unit.board.views.afternoon import world

if TYPE_CHECKING:
    from pathlib import Path


def test_the_open_panel_is_the_header_the_tabs_and_the_overview(tmp_path: Path) -> None:
    found = panel(world(tmp_path), SLUG, "overview")
    assert found.overview is not None
    assert expected.OPEN.overview is not None
    for name in ("review", "building", "verdict", "now", "phases"):
        assert getattr(found.overview, name) == getattr(expected.OVERVIEW, name), name
    assert found == expected.OPEN


def test_the_merge_step_draws_the_header_with_no_act_and_no_current_tab(
    tmp_path: Path,
) -> None:
    found = panel(world(tmp_path), SLUG, "merge")
    assert found.merge == expected.MERGE
    assert found == expected.MERGE_STEP


def test_an_address_that_names_no_task_is_the_panel_that_says_so(
    tmp_path: Path,
) -> None:
    found = panel(world(tmp_path), "no-such-task", "overview")
    assert found.missing is not None
    assert found.head is None
    assert (
        found.missing.said == "No task “no-such-task” is on record in this repository."
    )
