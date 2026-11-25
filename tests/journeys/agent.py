"""The commands of a task's session and its agents, as the journeys of this folder run them: each
through the tree in this process with `--repo` to the journey's own repository, on the world of
`tests/journeys/test_skeleton.py`."""

from typing import TYPE_CHECKING

from fakes.repo import run_git, write
from journeys.test_skeleton import JOURNEY, lem, parses

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

    from journeys.test_skeleton import Envelope, World

    type Capsys = pytest.CaptureFixture[str]


def ok(
    capsys: Capsys,
    world: World,
    *argv: str,
    inside: bool = False,
    at: Path | None = None,
) -> Envelope:
    """`lem ARGV` in the main checkout, in the task's worktree when `inside`, or in the folder
    `at`; it succeeds, and the command its envelope names next is one the tree takes."""
    where = at or (world.worktree if inside else world.checkout)
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


SMALL_CRITERIA = """## Acceptance criteria

Size: small, because it is one file.

1. {text}
"""
NO_TEST = "   - no test: the change keeps behavior; the suite holds it\n"
CLEAN_READ = {
    "kind": "read",
    "ran": [{"name": "claude", "why": "one read of one file"}],
    "left_out": [],
    "answered": ["claude"],
    "silent": [],
    "must_fix": 0,
    "should": 0,
    "nit": 0,
    "outside": [],
    "careful": False,
    "careful_why": "one file reaches nothing that must never go wrong",
}


def worktree_of(world: World, slug: str) -> Path:
    return world.checkout / ".lem" / "worktrees" / slug


def small_built(
    capsys: Capsys,
    world: World,
    slug: str,
    files: dict[str, str],
    subject: str,
    *opening: str,
    opened: bool = False,
) -> None:
    """A fast-track task `slug` opened (with the words `opening` too) unless it is `opened`
    already, approved by Lem in the owner's name, built with one commit of `files`, and
    `ready`."""
    if not opened:
        ok(capsys, world, "task", "open", slug, "--ask", subject, *opening)
    read = ("--type", "fix", "--why", "one file", "--track", "small", "--then", "fast")
    ok(capsys, world, "task", "read", slug, *read)
    folder = world.checkout / ".lem" / "state" / "tasks" / slug
    (folder / "criteria.md").write_text(SMALL_CRITERIA.format(text=subject))
    ok(capsys, world, "criteria", "approve", slug, "--small")
    ok(capsys, world, "task", "worktree", slug)
    ok(capsys, world, "task", "move", slug, "building", "--line", "one builder")
    where = worktree_of(world, slug)
    write(where, {name: body.encode() for name, body in files.items()})
    run_git(where, "add", "--all")
    run_git(where, "commit", "--quiet", "--message", subject)
    with (folder / "criteria.md").open("a") as criteria:
        criteria.write(NO_TEST)
    ok(capsys, world, "criteria", "record", slug, at=where)
    ok(capsys, world, "task", "move", slug, "ready", "--line", "built")


def small_landed(capsys: Capsys, world: World, slug: str, subject: str) -> None:
    """The landing of the ready fast-track task `slug`, each step the one `lem land next`
    names, to its cleanup."""
    while (verb := ok(capsys, world, "land", "next", slug)["result"]["step"]) != "done":
        words: tuple[str, ...] = ()
        if verb == "read":
            told = ok(capsys, world, "land", "read", slug)["result"]
            said = {**CLEAN_READ, "attempt": told["attempt"], "tip": told["tip"]}
            words = ("--record", world.written(f"{slug}-read.json", said))
        elif verb == "propose":
            words = ("--title", subject, "--notes", world.written("none.md", "none\n"))
        elif verb == "merge-review":
            told = ok(capsys, world, "land", "merge-review", slug)["result"]
            reply = world.written(f"{slug}-reply.md", "Verdict: merge\n\nOne file.\n")
            words = ("--file", reply, "--tip", told["tip"], "--base", told["base"])
        elif verb == "merge":
            words = ("--by", "merger", "--message", subject)
        ok(capsys, world, "land", verb, slug, *words)
