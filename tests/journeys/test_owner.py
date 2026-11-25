"""The owner away and back, with what waits for him: his word is the machine's mark, the shape
goes on without him while he is away, and a request whose criteria nobody of his approved is not
green and waits for his merge (`stages/away.md`; `lem waiting`, `lem owner away|back|watch`).
"""

from typing import TYPE_CHECKING

import pytest

from journeys.agent import ok
from journeys.test_skeleton import SLUG, made
from journeys.test_standard_track import CRITERIA, built, planned, prepared, step

if TYPE_CHECKING:
    from pathlib import Path

    from journeys.test_skeleton import Envelope, World

type Capsys = pytest.CaptureFixture[str]

INTERVIEW = (
    "--type",
    "docs",
    "--why",
    "a word of the README and its check",
    "--track",
    "full",
    "--then",
    "interview",
    "--wait",
    "interview",
)
WAITS = "the interview waits for the owner"


def waiting(capsys: Capsys, world: World) -> Envelope:
    return ok(capsys, world, "waiting")["result"]


def held(capsys: Capsys, world: World) -> list[tuple[str, str]]:
    return [(one["task"], one["line"]) for one in waiting(capsys, world)["held"]]


def interviewed(capsys: Capsys, world: World) -> None:
    """A request of the standard track whose interview waits for the owner."""
    ok(capsys, world, "task", "open", SLUG, "--ask", "the README says recieve")
    ok(capsys, world, "task", "read", SLUG, *INTERVIEW)


def test_his_away_and_back_hold_for_the_machine_and_what_waits_follows_his_word(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    interviewed(capsys, world)
    found = waiting(capsys, world)
    assert found["owner"] == {"away": False, "since": None, "words": None, "seen": 0}
    assert held(capsys, world) == [(SLUG, WAITS)]
    away = ok(capsys, world, "owner", "away", "--words", "I'm away till Monday")
    result = away["result"]
    assert (result["away"], result["written"], result["tasks"], result["seen"]) == (
        True,
        True,
        [SLUG],
        1,
    )
    again = ok(capsys, world, "owner", "away", "--words", "away")["result"]
    assert (again["written"], again["words"]) == (False, "I'm away till Monday")
    assert held(capsys, world) == []
    watched = ok(capsys, world, "owner", "watch", "--seen", "0")["result"]
    assert (watched["away"], watched["seen"]) == (True, 1)
    other = made(tmp_path / "another-repository", monkeypatch)
    assert waiting(capsys, other)["owner"]["away"] is True
    back = ok(capsys, world, "owner", "back", "--words", "I'm back")["result"]
    assert (back["away"], back["written"], back["seen"]) == (False, True, 2)
    assert held(capsys, world) == [(SLUG, WAITS)]
    assert waiting(capsys, other)["owner"]["words"] == "I'm back"


def test_criteria_approved_while_he_was_away_make_the_request_not_green_for_his_merge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    interviewed(capsys, world)
    ok(capsys, world, "owner", "away", "--words", "I'm away till Monday")
    guess = ("--what", "Which word?", "--chose", "receive", "--why", "the dictionary")
    ok(capsys, world, "decisions", "log", SLUG, "--by", "lem", *guess)
    answered = world.written("criteria.md", CRITERIA)
    digest = ok(capsys, world, "criteria", "digest", SLUG, "--file", answered)
    ok(capsys, world, "criteria", "read", SLUG, "start", "--by", "lem")
    read = (
        *("done", "--by", "lem", "--asked", "2", "--answered", "2"),
        *("--family", "claude", "--family", "codex", "--criteria", "1"),
        *("--flagged", "0", "--digest", digest["result"]["digest"]),
    )
    ok(capsys, world, "criteria", "read", SLUG, *read)
    approved = ok(
        capsys, world, "criteria", "approve", SLUG, "--file", answered, "--alone"
    )
    assert approved["result"]["by"] == "alone"
    assert held(capsys, world) == []
    back = ok(capsys, world, "owner", "back", "--words", "I'm back")["result"]
    assert back["tasks"] == [SLUG]
    built(capsys, world, planned(capsys, world))
    prepared(capsys, world)
    proposed = step(capsys, world, "propose")["result"]
    assert (proposed["green"], proposed["who_acts"]) == (False, "owner")
    day = approved["result"]["at"][:10]
    why = f"they were approved on {day} while the task ran without the owner"
    assert proposed["reasons"] == [f"the owner did not approve the criteria: {why}"]
    told = step(capsys, world, "merge-review")["result"]
    reply = world.written("reply.md", "Verdict: call\n\nHis criteria wait for him.\n")
    pinned = ("--tip", told["tip"], "--base", told["base"])
    ok(capsys, world, "land", "merge-review", SLUG, "--file", reply, *pinned)
    due = ok(capsys, world, "land", "next", SLUG)
    assert (due["result"]["by"], due["next"]["do"]) == ("owner", "wait")
    assert world.forge.merge_calls == []
