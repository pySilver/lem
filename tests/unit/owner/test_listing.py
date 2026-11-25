"""`lem waiting` on a workspace: each group with the facts of its kind, the board's rows and
stacks, the count, one task's, the forge's conflict and last night's report (`main`:
`tests/lem-decisions.sh` "waiting lists in one JSON what waits for the owner", "a task queued
after a dropped task", "in the morning the list marks a task the night held";
`tests/lem-serve.sh` "lem project waiting lists the rows of the board's Waits for you")."""

from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING

import msgspec

from fakes.command import lem
from fakes.records import MOMENT
from lem.app.owner import listing
from lem.records.holds import Blocked, BreakerHold, OwnerHold, Parked
from lem.records.landing.record import Landing
from lem.store import tasks
from unit.owner.looked import opened, proposed, read
from unit.task.spaces import made, refusal, result, workspace

if TYPE_CHECKING:
    from pathlib import Path

    from lem.store.places import Workspace

NOW = MOMENT + timedelta(hours=1)
NIGHT = date(2026, 11, 25)


def put_open(where: Workspace, slug: str, landing: Landing) -> None:
    record = opened(slug).record
    tasks.create(where.state, msgspec.structs.replace(record, landing=landing))


def test_each_group_holds_the_rows_of_its_kind_with_its_facts(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(
        where,
        "stopped-build",
        status="building",
        hold=BreakerHold(number=2, since=MOMENT),
    )
    line = "the criteria wait for the owner"
    made(
        where,
        "approve-me",
        status="shaping",
        hold=OwnerHold(on="criteria", line=line, since=MOMENT),
    )
    blocked = Blocked(
        why="a builder ended twice", fix="tell it what to do", since=MOMENT
    )
    made(where, "stuck", status="landing", hold=blocked)
    made(where, "first", status="dropped")
    made(where, "second", status="queued", after="first")
    made(where, "aside", status="planned", hold=Parked(since=MOMENT, words="later"))
    landing = opened(
        "merge-me", proposed=proposed(green=False, who="owner"), reads=(read("call"),)
    )
    put_open(where, "merge-me", landing.record.landing or Landing())
    found = result(lem("waiting", cwd=tmp_path))
    assert [entry["task"] for entry in found["criteria"]] == ["approve-me"]
    assert found["criteria"][0]["line"] == line
    assert found["blocked"][0] | {"since": None} == {
        "task": "stuck",
        "ask": "fix the login",
        "since": None,
        "night": None,
        "line": "a builder ended twice",
        "fix": "tell it what to do",
    }
    after = found["after_dropped"][0]
    assert (after["task"], after["after"], after["start"], after["drop"]) == (
        "second",
        "first",
        "start second now",
        "/lem drop second",
    )
    pull = found["pull_requests"][0]
    assert (pull["pull_request"]["number"], pull["green"], pull["not_green"]) == (
        44,
        False,
        ["the review left a must-fix"],
    )
    assert pull["merge_review"]["verdict"] == "call"
    assert found["reviews"][0]["why"] == "Verdict: call. It needs you."
    assert [one["task"] for one in found["parked"]] == ["aside"]
    stacked = [
        (one["task"], [thing["kind"] for thing in one["things"]])
        for one in found["tasks"]
    ]
    assert stacked == [
        ("stopped-build", ["breaker"]),
        ("approve-me", ["criteria"]),
        ("second", ["after_dropped"]),
        ("stuck", ["blocked"]),
        ("merge-me", ["review", "merge"]),
    ]
    assert found["count"] == 5
    assert [row["key"] for row in found["rows"]][-2:] == [
        "review:merge-me",
        "merge:merge-me",
    ]
    assert found["sessions"] == {"known": True, "said": None}


def test_a_task_named_lists_only_its_own(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, "first", status="dropped")
    made(where, "second", status="queued", after="first")
    made(where, "third", status="queued", after="first")
    found = result(lem("waiting", "--task", "third", cwd=tmp_path))
    assert [row["task"] for row in found["rows"]] == ["third"]
    assert found["count"] == 1
    assert refusal(lem("waiting", "--task", "nobody", cwd=tmp_path))["code"]


def test_the_breaker_is_as_decisions_pending_gives_it(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    breaker = BreakerHold(number=1, since=MOMENT)
    made(where, "stopped-build", status="building", hold=breaker)
    found = result(lem("waiting", cwd=tmp_path))
    pending = result(lem("decisions", "pending", cwd=tmp_path))
    assert found["breakers"] == pending["waiting"]


def test_the_report_of_last_night_and_no_older_one(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    nights = where.state / "night"
    nights.mkdir()
    (nights / "2026-11-23.md").write_text("old", encoding="utf-8")
    assert listing.night_report(where.state, NIGHT) is None
    (nights / "2026-11-24.md").write_text("last night", encoding="utf-8")
    found = listing.night_report(where.state, NIGHT)
    assert found is not None
    assert (found.date, found.path) == (
        date(2026, 11, 24),
        str(nights / "2026-11-24.md"),
    )
    raw = msgspec.json.decode(msgspec.json.encode(found))
    assert raw == {"date": "2026-11-24", "file": str(nights / "2026-11-24.md")}


def test_a_nights_pull_request_and_held_task_carry_its_night(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    order = OwnerHold(on="order", line="the order waits for the owner", since=MOMENT)
    made(where, "night-order", status="queued", hold=order, night=NIGHT, mode="alone")
    found = result(lem("waiting", cwd=tmp_path))
    assert [(one["task"], one["night"]) for one in found["held"]] == [
        ("night-order", "2026-11-25")
    ]


def test_the_forges_conflict_at_the_proposed_head(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    landing = opened(
        "merge-me", proposed=proposed(green=False, who="owner"), reads=(read("call"),)
    ).record.landing
    put_open(where, "merge-me", landing or Landing())
    tip = "a" * 40
    look = {
        "looked": "2026-11-25T10:30:00Z",
        "seen": {"merge-me": {"head": tip, "mergeable": "CONFLICTING"}},
    }
    (where.state / "forge.json").write_bytes(msgspec.json.encode(look))
    found = result(lem("waiting", cwd=tmp_path))
    assert found["pull_requests"][0]["conflict"] is True
    things = found["tasks"][0]["things"]
    assert [one["verb"] for one in things] == [
        "Read the merge review",
        "It conflicts with the base",
    ]
    assert found["forge"] == {"looked": "2026-11-25T10:30:00Z"}


def test_while_he_is_away_the_list_says_so_and_his_criteria_go_on(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    line = "the criteria wait for the owner"
    made(
        where,
        "approve-me",
        status="shaping",
        hold=OwnerHold(on="criteria", line=line, since=MOMENT),
    )
    made(
        where,
        "stopped-build",
        status="building",
        hold=BreakerHold(number=1, since=MOMENT),
    )
    lem("owner", "away", "--words", "I'm away", cwd=tmp_path)
    found = result(lem("waiting", cwd=tmp_path))
    assert found["owner"]["away"] is True
    assert found["criteria"] == []
    assert [row["kind"] for row in found["rows"]] == ["breaker"]
    assert datetime.fromisoformat(found["owner"]["since"]).tzinfo == UTC
