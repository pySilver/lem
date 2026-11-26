"""A command that a refusal or a brief gives for a shell keeps a path with a space as one word:
the step lock to remove, the main checkout of another repository, the board's workspace, and
the review's rules."""

import shlex
from pathlib import Path

import pytest

from fakes.repo import RealRepo
from lem.app.tasks import where
from lem.board import boards
from lem.kernel.errors import Refusal
from lem.store import places, step_refusals

SPACED = Path("/a workspace/shop")


def command_in(text: str, start: str) -> list[str]:
    """The words of the command in `text` that begins with `start`, as a shell splits them,
    up to the end of its parentheses or its sentence."""
    tail = start + text.split(start, 1)[1]
    return shlex.split(tail.split(")", 1)[0].split(", then", 1)[0])


def test_the_step_lock_to_remove_is_one_word() -> None:
    lock = SPACED / ".lem/state/tasks/fix-the-login/step.lock"
    said = step_refusals.unopened(
        lock, "fix-the-login", "checks", OSError(13, "denied")
    )
    assert command_in(said.fix, "rm -r") == ["rm", "-r", str(lock)]


def test_the_other_main_checkout_is_one_word(tmp_path: Path) -> None:
    here = RealRepo.init(tmp_path / "here", {"README.md": b"hello\n"}).checkout
    (here / ".lem").mkdir()
    workspace = places.workspace(here)
    with pytest.raises(Refusal) as refused:
        where.checkout_refusal(workspace, tmp_path / "a workspace")
    words = command_in(refused.value.fix, "lem --repo")
    assert words[:3] == ["lem", "--repo", str(tmp_path / "a workspace")]


def test_the_workspace_to_add_to_the_board_is_one_word(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    checkout = tmp_path / "a workspace"
    checkout.mkdir()
    with pytest.raises(Refusal) as refused:
        boards.board_of(home, "http://127.0.0.1:1", checkout)
    words = shlex.split(refused.value.fix)
    assert words == ["lem", "serve", "add", str(checkout.resolve())]
