"""The commands of a task's session and its agents, as the journeys of this folder run them: each
through the tree in this process with `--repo` to the journey's own repository, on the world of
`tests/journeys/test_skeleton.py`."""

from typing import TYPE_CHECKING

from journeys.test_skeleton import JOURNEY, lem, parses

if TYPE_CHECKING:
    import pytest

    from journeys.test_skeleton import Envelope, World

    type Capsys = pytest.CaptureFixture[str]


def ok(capsys: Capsys, world: World, *argv: str, inside: bool = False) -> Envelope:
    """`lem ARGV` in the main checkout, or in the task's worktree when `inside`; it succeeds,
    and the command its envelope names next is one the tree takes."""
    where = world.worktree if inside else world.checkout
    envelope = lem(capsys, where, *argv)
    assert envelope["ok"] is True, envelope
    parses(envelope)
    return envelope


def refused(capsys: Capsys, world: World, *argv: str) -> dict[str, str]:
    """`lem ARGV` in the main checkout, refused: its refusal, with exit 1."""
    envelope = lem(capsys, world.checkout, *argv)
    assert (envelope["ok"], envelope["code"]) == (False, 1), envelope
    return envelope["refusal"]


def through(capsys: Capsys, world: World, count: int) -> None:
    """The first `count` steps of the fast track's journey of `test_skeleton`."""
    for _, run in JOURNEY[:count]:
        envelope = run(capsys, world)
        assert envelope["ok"] is True, envelope


# The steps of the skeleton's journey after which its task is in each status.
SHAPING = 2
BUILDING = 6
READY = 10
LANDING = 11
OPEN = 17
