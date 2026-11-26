"""The header of a task's panel and its tabs (`main`'s `board_task.head`, `facts`, `key_line`,
`head_acts`, `tags` and `tab_nav`)."""

from typing import TYPE_CHECKING

import pytest

from fixtures.board import panel
from fixtures.board.receipt import SLUG
from lem.board.views import owed, standing
from lem.board.views.artifacts import named
from lem.board.views.panel.head import head
from lem.board.views.panel.tabs import tabs
from unit.board.views.afternoon import world

if TYPE_CHECKING:
    from pathlib import Path

    from lem.board.inputs.task.head import TaskHead
    from lem.board.views.world import World


def drawn(afternoon: World, slug: str, *, acting: bool = True) -> TaskHead:
    """The header of task `slug` of `afternoon`."""
    seen = owed.seen(afternoon, slug)
    rows = owed.of_task(afternoon, slug)
    return head(afternoon, seen, rows, standing.standing(seen, rows), acting=acting)


def test_the_refund_lines_header_is_the_one_the_board_draws(tmp_path: Path) -> None:
    afternoon = world(tmp_path)
    found = drawn(afternoon, SLUG)
    for name in ("pill", "key_line", "acts", "ask", "chips"):
        assert getattr(found, name) == getattr(panel.HEAD, name), name
    assert found.facts == panel.HEAD.facts
    assert found == panel.HEAD


def test_a_step_of_an_act_draws_the_header_with_no_act(tmp_path: Path) -> None:
    found = drawn(world(tmp_path), SLUG, acting=False)
    assert found.acts is None


def test_the_five_tabs_count_documents_and_loose_artifacts(tmp_path: Path) -> None:
    afternoon = world(tmp_path)
    assert tabs(afternoon, SLUG, "overview", 11) == panel.tabs("overview")
    assert tabs(afternoon, SLUG, "", 11) == panel.tabs("")


@pytest.mark.parametrize("suffix", ["", "-2", "-2-3"])
def test_the_map_names_a_merge_brief_with_its_round_and_dispatch(suffix: str) -> None:
    tip, base = "a" * 12, "b" * 12
    found = named.brief(f"merge-brief-{tip}-{base}{suffix}.md")
    assert found is not None
    assert found.title == "The merge agent's brief of aaaaaaaaa on bbbbbbbbb"
