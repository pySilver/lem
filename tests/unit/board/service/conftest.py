"""The fixtures of the board service's cases: the board with its door closed, and open."""

from typing import TYPE_CHECKING

import pytest

from lem.board.door import Door
from unit.board.service.given import DOOR, MAC, OWNER, Board, made

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def board(tmp_path: Path) -> Board:
    """The board with the door closed."""
    return made(tmp_path, None)


@pytest.fixture
def opened(tmp_path: Path) -> Board:
    """The board with the door open for the owner's login."""
    door = Door(name=MAC, port=DOOR, owner=OWNER, reread=lambda before: before)
    return made(tmp_path, door)
