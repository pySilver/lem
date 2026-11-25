"""The view Tasks of the afternoon, from its records: the four columns of
`fixtures.board.columns`, each card with its line, its time and its chips, and the rules of
who acts that `main`'s `tests/unit/test_board_model.py` held for the kanban."""

from typing import TYPE_CHECKING

from fixtures.board import columns
from lem.board.views import tasks
from unit.board.views.afternoon import world

if TYPE_CHECKING:
    from pathlib import Path


def test_the_afternoons_four_columns_are_todays(tmp_path: Path) -> None:
    shown = tasks.tasks(world(tmp_path))
    for made, expected in zip(shown.columns, columns.TASKS.columns, strict=True):
        assert made.cards == expected.cards, made.key
    assert shown == columns.TASKS
