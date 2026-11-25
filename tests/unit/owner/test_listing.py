"""`lem waiting` on a workspace: each group with the facts of its kind, the board's rows and
stacks, the count, one task's, the forge's conflict and last night's report (`main`:
`tests/lem-decisions.sh` "waiting lists in one JSON what waits for the owner", "a task queued
after a dropped task", "in the morning the list marks a task the night held";
`tests/lem-serve.sh` "lem project waiting lists the rows of the board's Waits for you")."""

from dataclasses import replace as replace_dataclass
from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING
from unittest.mock import patch

import msgspec
import pytest
from msgspec.structs import replace

from fakes.command import lem
from fakes.records import MOMENT
from fakes.repo import RealRepo, run_git
from lem.app.landing import reconcile
from lem.app.owner import listing, looking, stacks
from lem.app.owner.scope import Scope
from lem.app.sessions import acts, here, log
from lem.kernel import clock
from lem.kernel.errors import Refusal
from lem.model.decisions import criterion
from lem.model.landing import merge, phases
from lem.model.owner import waiting
from lem.model.owner.looks import Row
from lem.model.task import release
from lem.ports.harness import Signs, Transcript
from lem.records.holds import Blocked, BreakerHold, OwnerHold, Parked
from lem.records.landing.merge import Merged
from lem.records.landing.record import Landing, Pull
from lem.records.sessions import SessionLine
from lem.store import sessions, tasks
from unit.landing.merges import BY_MERGER, facing
from unit.landing.merges import opened as proposed_landing
from unit.landing.worlds import CRITERION, TREE
from unit.owner.looked import opened, proposed, read
from unit.sessions.harness import SigningHarness
from unit.sessions.terminal import AGENT, CALLER, with_caller
from unit.sessions.world import here_of
from unit.task.spaces import SETTINGS, made, refusal, result, workspace

if TYPE_CHECKING:
    from pathlib import Path

    from lem.model.owner.looks import Look
    from lem.store.places import Workspace

NOW = MOMENT + timedelta(hours=1)
NIGHT = date(2026, 11, 25)


def test_waiting_shows_the_review_of_the_base_that_returned(tmp_path: Path) -> None:
    repo = RealRepo.init(tmp_path, {"README.md": b"base A\n"})
    where = workspace(repo.checkout)
    base_a = run_git(repo.checkout, "rev-parse", "origin/main")
    tree_a = run_git(repo.checkout, "rev-parse", "origin/main^{tree}")
    base_b = repo.outside_commit("main", {"README.md": b"base B\n"})
    run_git(repo.checkout, "fetch", "origin")
    tree_b = run_git(repo.checkout, "rev-parse", "origin/main^{tree}")
    call = replace(read("call"), base=base_a, base_tree=tree_a)
    safe = replace(
        read("merge", why="Base B is safe."), base=base_b, base_tree=tree_b, at=NOW
    )
    task = opened(proposed=proposed(), reads=(call, safe)).record
    tasks.create(where.state, task)
    base_again = repo.outside_commit("main", {"README.md": b"base A\n"})
    run_git(repo.checkout, "fetch", "origin")
    assert base_again != base_a
    assert run_git(repo.checkout, "rev-parse", "origin/main^{tree}") == tree_a
    world = facing(tip=call.tip, base=base_again, base_tree=tree_a)
    assert phases.opened(task, world).by == "owner"

    found = result(lem("waiting", cwd=repo.checkout))
    assert [row["kind"] for row in found["rows"]] == ["review", "merge"]
    assert found["reviews"][0]["why"] == call.why
    assert found["pull_requests"][0]["merge_review"]["base_tree"] == tree_a


def test_waiting_does_not_ask_for_a_merge_after_the_forge_merged_it(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    task = opened(proposed=proposed(), reads=(read("call"),)).record
    merged = Merged(
        by="owner",
        via="board",
        commit="e" * 40,
        merged_head="a" * 40,
        parent="b" * 40,
        destination="main",
        base_checked="b" * 40,
        base_merged="b" * 40,
        at=NOW,
        text_updated=False,
    )
    changed = reconcile.taken(task, found=merged)
    assert changed.task.status == "open"
    due = phases.settled(changed)
    assert due is not None and due.step == "merged"
    tasks.create(where.state, changed)

    found = result(lem("waiting", cwd=tmp_path))
    assert found["reviews"] == found["pull_requests"] == found["rows"] == []


def test_waiting_uses_the_current_setting_for_who_merges(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    record = proposed_landing()
    tasks.create(where.state, record)
    assert result(lem("waiting", cwd=tmp_path))["rows"] == []
    (where.lem / "settings.toml").write_text(
        SETTINGS + 'land = "owner"\n', encoding="utf-8"
    )
    world = facing()
    current = replace(world, rules=replace(world.rules, land="owner"))
    stopped = merge.decide(record, current, BY_MERGER, TREE)
    assert isinstance(stopped, Refusal) and stopped.code == "merger-rule"

    found = result(lem("waiting", cwd=tmp_path))
    assert [row["kind"] for row in found["rows"]] == ["review", "merge"]
    assert found["reviews"][0]["why"] == merge.LAND_OWNER


def test_waiting_shows_the_criterion_change_that_bars_the_merge_agent(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    record = proposed_landing()
    assert not isinstance(merge.decide(record, facing(), BY_MERGER, TREE), Refusal)
    asked = criterion.Asked(
        how="changed",
        number=CRITERION.number,
        was=CRITERION.text,
        now="The login works with a hardware key.",
        why="the login requires a hardware key",
        by="lead",
    )
    changed = criterion.recorded(record, asked=asked, now=NOW)
    refusal = merge.decide(changed, facing(), BY_MERGER, TREE)
    assert isinstance(refusal, Refusal)
    assert refusal.code == "merger-rule"
    tasks.create(where.state, changed)
    found = result(lem("waiting", cwd=tmp_path))
    assert [row["kind"] for row in found["rows"]] == ["review", "merge"]
    assert found["reviews"][0]["why"] in refusal.why
    pull = found["pull_requests"][0]
    assert pull["green"] is False
    assert any("criterion 1 changed" in line for line in pull["not_green"])


def test_waiting_constructs_keyed_rows_in_keyed() -> None:
    given = (
        Row(kind="breaker", key="breaker:gift-note:2", task="gift-note", since=MOMENT),
        Row(kind="plan", key="plan:read-me", task="read-me", since=MOMENT),
    )
    with patch.object(stacks, "key_of", create=True, side_effect=AssertionError):
        found = stacks.keyed(Scope(rows=given, looks={}, slug=None))
    assert [(row.key, row.kind, row.task) for row in found] == [
        (row.key, row.kind, row.task) for row in given
    ]


def put_open(
    where: Workspace, slug: str, landing: Landing, *, night: date | None = None
) -> None:
    record = opened(slug).record
    task = replace(record.task, night=night, mode="alone") if night else record.task
    tasks.create(where.state, replace(record, landing=landing, task=task))


def test_waiting_projects_a_release_stop_before_any_command_writes_it(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    old = replace(opened("old-task").record, release="0.2.0")
    prior = replace(opened("prior-task").record, release=release.BEFORE)
    tasks.create(where.state, old)
    tasks.create(where.state, prior)
    found = result(lem("waiting", cwd=tmp_path))
    assert [(row["kind"], row["task"]) for row in found["rows"]] == [
        ("blocked", "old-task"),
        ("merge", "prior-task"),
    ]
    assert (
        "/lem drop old-task, then /lem resume old-task" in found["blocked"][0]["line"]
    )
    assert found["blocked"][0]["since"] == "2026-11-25T10:00:00Z"
    assert tasks.read(where.state, "old-task").task.hold is None


def test_waiting_refuses_broken_settings_before_it_reads_the_forge(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path, settings="[branch")
    (where.state / "forge.json").write_text("not json", encoding="utf-8")
    refused = refusal(lem("waiting", cwd=tmp_path))
    assert refused["code"] == "settings-toml"
    assert ".lem/settings.toml" in refused["why"]


def test_waiting_keeps_the_owner_rows_when_the_forge_cache_is_bad(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    made(
        where,
        "stopped-build",
        status="building",
        hold=BreakerHold(number=2, since=MOMENT),
    )
    criteria = OwnerHold(on="criteria", line="approve the criteria", since=MOMENT)
    made(where, "approve-me", status="shaping", hold=criteria)
    path = where.state / "forge.json"
    path.write_text("not json", encoding="utf-8")
    found = result(lem("waiting", cwd=tmp_path))
    assert [row["kind"] for row in found["rows"] if row["kind"] != "session"] == [
        "breaker",
        "criteria",
    ]
    assert found["forge"]["looked"] is None
    assert "forge.json" in found["forge"]["said"]
    assert path.read_text(encoding="utf-8") == "not json"


def test_waiting_uses_one_task_snapshot_for_its_sessions(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, "gift-note")
    with patch.object(tasks, "every", wraps=tasks.every) as every:
        found = looking.looked(here.bound(tmp_path), NOW)
    assert [one.record.task.slug for one in found.looks] == ["gift-note"]
    every.assert_called_once_with(where.state)


def working_look(tmp_path: Path, *, plan: bool, own: bool) -> Look:
    terminal, harness = with_caller(), SigningHarness()
    terminal.grounds[CALLER.id] = AGENT
    site = here_of(tmp_path, terminal, harness)
    if not own:
        site = replace_dataclass(site, caller="S-OTHER")
    slug = "gift-note"
    hold = (
        OwnerHold(on="plan", line="read the plan", since=MOMENT)
        if plan
        else BreakerHold(number=2, since=MOMENT)
    )
    made(site.where, slug, status="planned" if plan else "building", hold=hold)
    log.append(
        site.folder(slug),
        acts.Open(session=CALLER.id, at=MOMENT, name=slug, phase="build", why="new"),
    )
    sessions.append(
        site.folder(slug),
        SessionLine(
            at=MOMENT,
            source="startup",
            claude="owner",
            transcript="/test/owner-transcript",
            pane=CALLER.id,
            task=slug,
        ),
    )
    harness.by_task[slug] = (Transcript(path="/test/owner-transcript", claude="owner"),)
    harness.signs_of["/test/owner-transcript"] = Signs(sign=NOW, turn="runs")
    (found,) = looking.looked(site, NOW).looks
    assert found.session is not None and found.session.live
    return found


@pytest.mark.parametrize(("own", "expected"), [(True, ["breaker"]), (False, [])])
def test_a_running_breaker_is_visible_to_its_own_session(
    tmp_path: Path, *, own: bool, expected: list[str]
) -> None:
    found = working_look(tmp_path, plan=False, own=own)
    assert [row.kind for row in waiting.rows((found,), away=False, now=NOW)] == expected


def test_a_plan_still_waits_for_the_owner_during_a_live_turn(tmp_path: Path) -> None:
    found = working_look(tmp_path, plan=True, own=False)
    assert found.session is not None and found.session.working
    assert [row.kind for row in waiting.rows((found,), away=False, now=NOW)] == ["plan"]


def test_waiting_groups_the_rows_once_to_build_and_count_the_stacks(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    made(
        where,
        "stopped-build",
        status="building",
        hold=BreakerHold(number=2, since=MOMENT),
    )
    with patch.object(waiting, "stacks", wraps=waiting.stacks) as stack:
        found = listing.listed(tmp_path, None, MOMENT, NIGHT)
    assert found.count == len(found.tasks) == 1
    stack.assert_called_once()


def test_each_group_holds_the_rows_of_its_kind_with_its_facts(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    start = clock.now()
    made(
        where,
        "stopped-build",
        status="building",
        opened=start,
        hold=BreakerHold(number=2, since=MOMENT),
    )
    line = "the criteria wait for the owner"
    made(
        where,
        "approve-me",
        status="shaping",
        opened=start,
        hold=OwnerHold(on="criteria", line=line, since=MOMENT),
    )
    blocked = Blocked(
        why="a builder ended twice", fix="tell it what to do", since=MOMENT
    )
    made(where, "stuck", status="landing", opened=start, hold=blocked)
    dropped_at = MOMENT + timedelta(minutes=5)
    made(where, "first", status="dropped", since=dropped_at)
    made(where, "second", status="queued", after=("first",))
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
    assert datetime.fromisoformat(after["since"]) == dropped_at
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
        ["the review left 1 must-fix"],
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
        ("stuck", ["blocked"]),
        ("second", ["after_dropped"]),
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
    made(where, "second", status="queued", after=("first",))
    made(where, "third", status="queued", after=("first",))
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
    made(where, "day-order", status="queued", hold=order)
    made(where, "night-order", status="queued", hold=order, night=NIGHT, mode="alone")
    for slug, number, night, green in (
        ("day-pull", 44, None, False),
        ("night-full", 45, NIGHT, False),
        ("night-small", 46, NIGHT, True),
    ):
        found = opened(
            slug,
            pull=Pull(
                number=number, url=f"https://github.com/o/r/pull/{number}", title=slug
            ),
            proposed=proposed(green=green, who="owner"),
            reads=(read("call"),),
        )
        assert found.record.landing is not None
        put_open(where, slug, found.record.landing, night=night)
    nights = where.state / "night"
    nights.mkdir()
    (nights / "2026-11-23.md").write_text("old", encoding="utf-8")
    assert listing.listed(tmp_path, None, NOW, NIGHT).night_report is None
    report = nights / f"{NIGHT.isoformat()}.md"
    report.write_text("the night's report", encoding="utf-8")
    found = listing.listed(tmp_path, None, NOW, NIGHT)
    assert [(one.task, one.night) for one in found.held] == [
        ("day-order", None),
        ("night-order", NIGHT),
    ]
    assert [(one.task, one.night, one.green) for one in found.pull_requests] == [
        ("day-pull", None, False),
        ("night-full", NIGHT, False),
        ("night-small", NIGHT, True),
    ]
    assert found.night_report == listing.NightReport(date=NIGHT, path=str(report))


@pytest.mark.parametrize(
    ("head", "conflict", "verb"),
    [
        ("a", True, "It conflicts with the base"),
        ("d", False, "Merge the pull request #44"),
    ],
)
def test_the_forges_conflict_at_the_proposed_head(
    tmp_path: Path, head: str, *, conflict: bool, verb: str
) -> None:
    where = workspace(tmp_path)
    landing = opened(
        "merge-me", proposed=proposed(green=False, who="owner"), reads=(read("call"),)
    ).record.landing
    put_open(where, "merge-me", landing or Landing())
    look = {
        "looked": "2026-11-25T10:30:00Z",
        "seen": {"merge-me": {"head": head * 40, "mergeable": "CONFLICTING"}},
    }
    (where.state / "forge.json").write_bytes(msgspec.json.encode(look))
    found = result(lem("waiting", cwd=tmp_path))
    assert found["pull_requests"][0]["conflict"] is conflict
    things = found["tasks"][0]["things"]
    assert [one["verb"] for one in things] == [
        "Read the merge review",
        verb,
    ]
    assert found["forge"] == {"looked": "2026-11-25T10:30:00Z"}


def test_while_he_is_away_the_list_says_so_and_his_criteria_go_on(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    start = clock.now()
    line = "the criteria wait for the owner"
    made(
        where,
        "approve-me",
        status="shaping",
        opened=start,
        hold=OwnerHold(on="criteria", line=line, since=MOMENT),
    )
    made(
        where,
        "stopped-build",
        status="building",
        opened=start,
        hold=BreakerHold(number=1, since=MOMENT),
    )
    lem("owner", "away", "--words", "I'm away", cwd=tmp_path)
    found = result(lem("waiting", cwd=tmp_path))
    assert found["owner"]["away"] is True
    assert found["criteria"] == []
    assert [row["kind"] for row in found["rows"]] == ["breaker"]
    assert datetime.fromisoformat(found["owner"]["since"]).tzinfo == UTC
