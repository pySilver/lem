"""The view Waits for you of the afternoon, from its records: the stacks of
`fixtures.board.waiting`, one for each task with something the owner does, the refund line's two
things in one, and the two tasks he parked."""

from typing import TYPE_CHECKING

from fixtures.board import waiting
from lem.board.views.waits import view
from unit.board.views.afternoon import world

if TYPE_CHECKING:
    from pathlib import Path


def test_the_afternoons_waits_are_todays(tmp_path: Path) -> None:
    shown = view.waits(world(tmp_path))
    for made, expected in zip(shown.stacks, waiting.WAITS.stacks, strict=True):
        for one, other in zip(made.waits, expected.waits, strict=True):
            assert one == other, one.id
        assert made == expected, made.id
    assert shown.parked == waiting.WAITS.parked
    assert shown == waiting.WAITS
    assert view.KEYS == waiting.KEYS
