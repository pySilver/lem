"""The night's run: a task opened from an item of the backlog with nobody at the terminal runs
without the owner to its pull request, which waits for his merge marked as the night's; and the
night that proposes adds its run to the day's record, whose proposals the reviewer judges into
items of the board's backlog that the owner drops (`stages/night.md`).
"""

from typing import TYPE_CHECKING

import pytest

from fakes.repo import run_git
from journeys.agent import CLEAN_READ, NO_TEST, SMALL_CRITERIA, ok, refused
from journeys.test_duties import served
from journeys.test_skeleton import SLUG, made
from lem.board.duties import runner
from lem.kernel import clock

if TYPE_CHECKING:
    from pathlib import Path

    from journeys.test_skeleton import Envelope, World

type Capsys = pytest.CaptureFixture[str]

NIGHT = "2026-11-25"
ITEM = "docs/backlog/the-readme-says-recieve.md"
ITEM_BODY = (
    b"---\nworth: yes\nwhere: README.md\nadded: 2026-11-24\n---\n"
    b"# The README says recieve\n\nThe README spells receive wrong.\n"
)
TITLE = "docs: the README says receive"


def opened(capsys: Capsys, world: World) -> str:
    """The night's task of the item: its ask and its item are the item's path, nobody at the
    terminal read it, and its criterion is approved without the owner. Return the approval's
    recorded moment."""
    ok(
        capsys,
        world,
        "task",
        "open",
        SLUG,
        "--ask",
        ITEM,
        "--item",
        ITEM,
        "--night",
        NIGHT,
    )
    read = ("--type", "docs", "--why", "a word", "--track", "small", "--then", "fast")
    ok(capsys, world, "task", "read", SLUG, *read, "--someone-else")
    criteria = world.task_folder / "criteria.md"
    criteria.write_text(SMALL_CRITERIA.format(text="The README says receive."))
    approved = ok(
        capsys, world, "criteria", "approve", SLUG, "--file", str(criteria), "--alone"
    )
    assert approved["result"]["by"] == "alone"
    return approved["result"]["at"]


def built(capsys: Capsys, world: World) -> None:
    """The builder's commit of the change; the item stays on the branch."""
    ok(capsys, world, "task", "worktree", SLUG)
    ok(capsys, world, "task", "move", SLUG, "building", "--line", "one builder")
    (world.worktree / "README.md").write_text("The README says receive.\n")
    run_git(world.worktree, "commit", "--quiet", "--all", "--message", TITLE)
    with (world.task_folder / "criteria.md").open("a") as criteria:
        criteria.write(NO_TEST)
    ok(capsys, world, "criteria", "record", SLUG, inside=True)
    ok(capsys, world, "task", "move", SLUG, "ready", "--line", "built", inside=True)


def onward(capsys: Capsys, world: World) -> list[str]:
    """The landing steps `lem land next` names, run until `propose` is due."""
    ran: list[str] = []
    while (
        verb := ok(capsys, world, "land", "next", SLUG)["result"]["step"]
    ) != "propose":
        words: tuple[str, ...] = ()
        if verb == "read":
            told = ok(capsys, world, "land", "read", SLUG)["result"]
            said = {**CLEAN_READ, "attempt": told["attempt"], "tip": told["tip"]}
            words = ("--record", world.written(f"read-{told['attempt']}.json", said))
        ok(capsys, world, "land", verb, SLUG, *words)
        ran.append(verb)
    return ran


def proposal(world: World) -> tuple[str, ...]:
    return (
        "land",
        "propose",
        SLUG,
        "--title",
        TITLE,
        "--notes",
        world.written("n.md", "none\n"),
    )


def test_a_night_task_of_an_item_runs_without_the_owner_to_a_request_he_merges(
    tmp_path: Path, own_home: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    served(world, own_home, monkeypatch)
    world.repo.outside_commit("main", {ITEM: ITEM_BODY})
    run_git(world.checkout, "pull", "--quiet", "--ff-only", "origin", "main")
    backlog = ok(capsys, world, "path", "backlog")["result"]
    assert (backlog["path"], backlog["exists"]) == (
        str(world.checkout / "docs/backlog"),
        True,
    )
    approved_at = opened(capsys, world)
    shown = ok(capsys, world, "task", "show", SLUG)["result"]
    assert (shown["night"], shown["mode"]) == (NIGHT, "alone")
    built(capsys, world)
    assert onward(capsys, world) == ["start", "base", "checks", "read"]
    held = refused(capsys, world, *proposal(world))
    assert held["code"] == "own-item"
    assert ITEM in held["why"]
    run_git(world.worktree, "rm", "--quiet", ITEM)
    run_git(
        world.worktree,
        "commit",
        "--quiet",
        "--message",
        "docs(backlog): the item is done",
    )
    assert "read" not in onward(capsys, world)
    proposed = ok(capsys, world, *proposal(world))["result"]
    approval_day = approved_at[:10]
    reason = (
        f"the owner did not approve the criteria: they were approved on {approval_day} "
        "while the task ran without the owner"
    )
    assert (proposed["green"], proposed["reasons"]) == (False, [reason])
    told = ok(capsys, world, "land", "merge-review", SLUG)["result"]
    reply = world.written(
        "reply.md", "Verdict: call\n\nThe night's criteria wait for him.\n"
    )
    pinned = ("--tip", told["tip"], "--base", told["base"])
    ok(capsys, world, "land", "merge-review", SLUG, "--file", reply, *pinned)
    runner.tick(own_home, clock.now())
    waits = ok(capsys, world, "waiting")["result"]
    nights = [one["night"] for one in waits["pull_requests"]]
    assert nights == [NIGHT]
    verbs = [thing["verb"] for one in waits["tasks"] for thing in one["things"]]
    assert verbs == ["Read the merge review", "Merge the pull request #1"]
    ok(capsys, world, "owner", "away", "--words", "away")
    ok(capsys, world, "owner", "back", "--words", "back")
    assert ok(capsys, world, "task", "show", SLUG)["result"]["mode"] == "alone"
    assert world.forge.merge_calls == []
    assert run_git(world.repo.origin, "show", f"refs/heads/docs/{SLUG}:README.md") == (
        "The README says receive."
    )


RUN = {
    "read": "the whole test suite, run twice in the main checkout",
    "proposals": [
        {
            "area": "tests",
            "move": "The refund check waits for its event, not for one second",
            "body": "the file, the change, and the run that failed: its output and its time",
            "source": "the first run of the suite this night",
            "where": "tests/test_refunds.py:test_refund_event",
        }
    ],
}
VERDICTS = {
    "verdicts": [{"proposal": f"night of {NIGHT} #1", "passed": "tests"}],
    "titles": {"tests": "The refund check waits for its event"},
}


def proposals(capsys: Capsys, world: World) -> Envelope:
    return ok(capsys, world, "proposals", "list")["result"]


def test_a_night_that_proposes_records_its_run_and_the_reviewers_item_waits_for_his_drop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    added = ok(
        capsys,
        world,
        "proposals",
        "add",
        "--kind",
        "night",
        "--date",
        NIGHT,
        "--file",
        world.written("run.json", RUN),
    )
    assert added["result"]["names"] == [f"night of {NIGHT} #1"]
    record = world.checkout / ".lem" / "state" / "night" / f"{NIGHT}.json"
    assert added["result"]["file"] == str(record)
    listed = proposals(capsys, world)
    assert [one["name"] for one in listed["undecided"]] == [f"night of {NIGHT} #1"]
    assert listed["newest"]["night"]["read"] == RUN["read"]
    judged = ok(
        capsys,
        world,
        "proposals",
        "verdict",
        "--file",
        world.written("v.json", VERDICTS),
    )
    (item,) = judged["result"]["items"]
    assert item["path"] == ".lem/state/backlog/the-refund-check-waits-for-its-event.md"
    assert (world.checkout / item["path"]).is_file()
    assert proposals(capsys, world)["undecided"] == []
    again = refused(
        capsys,
        world,
        "proposals",
        "verdict",
        "--file",
        world.written("v.json", VERDICTS),
    )
    assert again["code"]
    dropped = ok(capsys, world, "proposals", "drop", item["path"])
    assert dropped["result"]["proposals"] == [f"night of {NIGHT} #1"]
    assert not (world.checkout / item["path"]).exists()
    assert run_git(world.checkout, "status", "--porcelain") == ""
