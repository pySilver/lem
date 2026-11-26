"""The hard paths of `landing.md` E that cross steps, each a journey of the whole app on a real
repository and `LocalForge`: a red base and its repair task, a ticket's step paid after the end,
and a review's open must-fix carried over a clean rebase to the server's merge of the owner's
standing merge.
"""

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pytest

from fakes.repo import run_git
from fakes.terminal import FakeTerminal
from journeys.agent import ok, refused, small_built, small_landed
from journeys.landing.test_base import landing
from journeys.landing.test_merge import moved, owner
from journeys.test_duties import served, ticked
from journeys.test_skeleton import REVIEW, SETTINGS, SLUG, SUBJECT, made, upto
from lem.app import wiring
from lem.kernel import clock
from lem.ports.place import Place
from lem.ports.terminal import Pane

if TYPE_CHECKING:
    from pathlib import Path

    from journeys.test_skeleton import Envelope, World
    from lem.adapters.notify_push_devices import Said

type Capsys = pytest.CaptureFixture[str]

REPAIR = "license-is-there"


def settings(world: World, text: bytes) -> None:
    """The team's settings of the main checkout, as the owner edited them."""
    (world.checkout / ".lem" / "settings.toml").write_bytes(text)


# ---- a red base ----


def test_a_red_base_waits_for_its_repair_task_and_lands_after_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "checks")
    red = SETTINGS.replace(b'"grep -q receive README.md"', b'"test -f LICENSE"')
    settings(world, red)
    said = refused(capsys, world, "land", "checks", SLUG)
    assert said["code"] == "red"
    assert "test -f LICENSE" in said["why"]
    small_built(
        capsys, world, REPAIR, {"LICENSE": "MIT\n"}, "fix: the LICENSE is there"
    )
    ok(capsys, world, "task", "red-base", SLUG, "--after", REPAIR)
    task = world.record()["task"]
    assert (task["hold"]["kind"], task["hold"]["after"]) == ("blocked", REPAIR)
    small_landed(capsys, world, REPAIR, "fix: the LICENSE is there")
    assert run_git(world.repo.origin, "show", "main:LICENSE") == "MIT"
    ok(
        capsys,
        world,
        "task",
        "move",
        SLUG,
        "ready",
        "--line",
        "the base is green again",
    )
    assert world.record()["task"].get("hold") is None
    small_landed(capsys, world, SLUG, SUBJECT)
    assert world.record()["task"]["status"] == "landed"
    assert (
        run_git(world.repo.origin, "show", "main:README.md")
        == "The README says receive."
    )
    assert len(world.forge.merge_calls) == 2


def test_a_red_base_keeps_its_hold_after_two_gone_sessions_and_a_dropped_repair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    terminal = wiring.bound(
        Place(checkout=world.checkout, home=tmp_path, environ={})
    ).terminal
    assert isinstance(terminal, FakeTerminal)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "claude"))
    terminal.caller = "S-MINE"
    terminal.panes["S-MINE"] = Pane(id="S-MINE", name="main", workspace="W-1")
    upto(capsys, world, "checks")
    red = SETTINGS.replace(b'"grep -q receive README.md"', b'"test -f LICENSE"')
    settings(world, red)
    assert refused(capsys, world, "land", "checks", SLUG)["code"] == "red"
    ok(capsys, world, "task", "open", REPAIR, "--ask", "restore the LICENSE")
    ok(capsys, world, "task", "red-base", SLUG, "--after", REPAIR)
    hold = world.record()["task"]["hold"]
    wait = ("session", "wait", REPAIR, "--until", "landed,dropped,answered")

    for why in ("new", "dead"):
        session = ok(capsys, world, "session", "open", REPAIR, "--why", why)
        pane = session["result"]["session"]
        terminal.close(pane, when_unselected=False)
        waited = ok(capsys, world, *wait)["result"]
        assert (waited["gone"], waited["session"]) == (True, pane)
        assert f"the session of {REPAIR} is gone" in waited["say"]

    assert [opening.name for opening in terminal.openings] == [REPAIR, REPAIR]
    assert world.record()["task"]["hold"] == hold
    ok(capsys, world, "task", "move", REPAIR, "dropped", "--line", "the owner drops it")
    ended = ok(capsys, world, *wait)["result"]
    assert ended["status"] == "dropped"
    assert not ended.get("gone", False)
    due = ok(capsys, world, "land", "next", SLUG)["result"]
    assert (due["step"], due["why"]) == ("wait", f"the base is red: {hold['fix']}")
    assert "on the owner's word" in due["why"]
    assert world.record()["task"]["hold"] == hold
    assert world.forge.merge_calls == []


# ---- a ticket's step after the end ----

LINEAR = SETTINGS + b'\n[tracker]\nkind = "linear"\n'


def test_a_ticket_step_owed_at_the_end_is_paid_after_it_and_the_ticket_stays_the_tasks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    settings(world, LINEAR)
    files = {"README.md": "The README says receive.\n"}
    small_built(capsys, world, "word-fix", files, SUBJECT, "--ticket", "ABC-12")
    ok(capsys, world, "task", "ticket", "word-fix", "started")
    shown = ok(capsys, world, "task", "show", "word-fix")["result"]["ticket"]
    assert shown == {"id": "ABC-12", "steps": ["started"]}
    small_landed(capsys, world, "word-fix", SUBJECT)
    shown = ok(capsys, world, "task", "show", "word-fix")["result"]
    assert shown["status"] == "landed"
    assert shown["ticket"]["owed"] == ["commented", "landed"]
    paid = ok(capsys, world, "task", "ticket", "word-fix", "commented")["result"]
    assert paid["owed"] == ["landed"]
    paid = ok(capsys, world, "task", "ticket", "word-fix", "landed")["result"]
    assert (paid["steps"], paid.get("owed")) == (
        ["started", "commented", "landed"],
        None,
    )
    again = refused(capsys, world, "task", "ticket", "word-fix", "landed")
    assert again["code"]
    taken = ("task", "open", "word-fix-again", "--ask", "ABC-12", "--ticket", "ABC-12")
    said = refused(capsys, world, *taken)
    assert said["code"] == "ticket-landed"
    assert "word-fix landed the ticket ABC-12" in said["why"]


# ---- an open must-fix carried over a clean rebase, to the server's merge ----

MUST_FIX = {**REVIEW, "must_fix": 1, "outside": []}
FIXED_WHY = "two rounds reviewed it: the last one left 1 must-fix"


def reviewed(capsys: Capsys, world: World, kind: str) -> Envelope:
    """The review that is due, recorded with one must-fix that stays open."""
    told = ok(capsys, world, "land", "read", SLUG)["result"]
    said = {**MUST_FIX, "kind": kind, "attempt": told["attempt"], "tip": told["tip"]}
    if kind == "round":
        said["ran"] = [{"name": "claude", "why": "the project's one profile"}]
    record = world.written(f"review-{told['attempt']}.json", said)
    return ok(capsys, world, "land", "read", SLUG, "--record", record)


def proposed(capsys: Capsys, world: World) -> Envelope:
    notes = world.written("notes.md", "none\n")
    return ok(
        capsys, world, "land", "propose", SLUG, "--title", SUBJECT, "--notes", notes
    )


def merge_read(capsys: Capsys, world: World, said: str) -> Envelope:
    told = ok(capsys, world, "land", "merge-review", SLUG)["result"]
    reply = world.written("reply.md", said)
    pinned = ("--tip", told["tip"], "--base", told["base"])
    return ok(capsys, world, "land", "merge-review", SLUG, "--file", reply, *pinned)


def test_an_open_must_fix_carries_over_a_clean_rebase_and_the_server_merges_his_standing_merge(
    tmp_path: Path, own_home: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    now = datetime(2026, 11, 26, tzinfo=UTC)
    monkeypatch.setattr(clock, "now", lambda: now)
    world = made(tmp_path, monkeypatch)
    served(world, own_home, monkeypatch)
    upto(capsys, world, "read")
    reviewed(capsys, world, "read")
    assert ok(capsys, world, "land", "next", SLUG)["result"]["step"] == "read"
    reviewed(capsys, world, "round")
    first = proposed(capsys, world)["result"]
    assert (first["green"], first["reasons"]) == (False, [FIXED_WHY])
    assert "The review carried" not in world.forge.bodies[1]
    called = merge_read(capsys, world, "Verdict: call\n\nThe must-fix is open.\n")
    assert called["next"]["do"] == "wait"
    moved(world)
    assert owner(capsys, world)["refusal"]["code"] == "base"
    assert landing(world)["standing"]["by_act"] == "session"
    ran = []
    while (
        verb := ok(capsys, world, "land", "next", SLUG)["result"]["step"]
    ) != "propose":
        ok(capsys, world, "land", verb, SLUG)
        ran.append(verb)
    assert ran == ["start", "base", "checks"]
    again = proposed(capsys, world)
    kept = landing(world)["proposed"]
    assert (kept["green"], kept["reasons"]) == (False, [FIXED_WHY])
    assert (kept["merge_review"], kept["owner_merge"]["state"]) == ("carried", "stands")
    assert kept["tip"] != first["tip"]
    assert len(landing(world)["reviews"]) == 2
    assert landing(world)["based"]["reviewed"] == first["tip"]
    assert landing(world)["reviews"][-1]["at"] == landing(world)["based"]["at"]
    assert landing(world)["reads"][-1]["carried_from"] == first["tip"]
    proposals = [
        entry for entry in world.record()["journal"] if entry["kind"] == "proposed"
    ]
    assert [(one["tip"], one["green"], one["reasons"]) for one in proposals] == [
        (first["tip"], False, [FIXED_WHY]),
        (kept["tip"], False, [FIXED_WHY]),
    ]
    second = proposals[1]
    assert (
        second["review_carry"],
        second["merge_review"],
        second["owner_merge"]["state"],
    ) == (
        "The review carried over the rebase, and its open must-fix.",
        "carried",
        "stands",
    )
    assert landing(world)["relands"] == 1
    assert (
        "lem land merge readme-says-receive --by owner --via server --standing"
        in (again["next"]["why"])
    )
    body = world.forge.bodies[1]
    assert body.startswith(f"**Not green.**\n\n- {FIXED_WHY}\n")
    assert "The merge review carries over the clean rebase." in body
    assert "The owner's merge stands: the change and its reasons stay." in body
    assert (
        "round 2 (a review round with the profiles that fit; answered: claude): "
        in body
    )
    assert "The review carried over the rebase, and its open must-fix." in body
    assert world.forge.merge_calls == []
    ticked(world, own_home, now)
    merged = landing(world)["merged"]
    assert (merged["by"], merged["via"], merged["merged_head"]) == (
        "owner",
        "server",
        kept["tip"],
    )
    assert len(world.forge.merge_calls) == 1
    ticked(world, own_home, now + timedelta(minutes=3))
    assert world.record()["task"]["status"] == "landed"
    assert run_git(world.repo.origin, "log", "-1", "--format=%s", "main") == SUBJECT


def test_two_failed_repairs_block_the_landing_on_the_board_and_send_one_push(
    tmp_path: Path, own_home: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    from journeys import test_standard_track as standard
    from journeys.test_acts import Board
    from lem.adapters.notify_push import PushNotifier
    from lem.board import machine
    from lem.board.push.watch import Watcher

    world = made(tmp_path, monkeypatch)
    standard.shaped(capsys, world)
    standard.built(capsys, world, standard.planned(capsys, world))
    for verb in ("start", "base", "polish"):
        ok(capsys, world, "land", verb, SLUG)
    ok(capsys, world, "land", "polish", SLUG, "--done")
    red = SETTINGS.replace(b'"grep -q receive README.md"', b'"test -f LICENSE"')
    settings(world, red)
    assert refused(capsys, world, "land", "checks", SLUG)["code"] == "red"
    repair = ("task", "span", SLUG, "builder")
    for _ in range(2):
        ok(capsys, world, *repair, "start", "--job", "the repair of a failed check")
        ok(capsys, world, *repair, "end", "--job", "the repair of a failed check")
        assert refused(capsys, world, "land", "checks", SLUG)["code"] == "red"

    board = Board(world)
    sent: list[Said] = []

    def told(
        _notifier: PushNotifier, push: Said, _names: tuple[str, ...]
    ) -> tuple[object, ...]:
        sent.append(push)
        return (object(),)

    monkeypatch.setattr(PushNotifier, "told", told)
    watcher = Watcher(own_home, machine.machine_name(), PushNotifier(own_home, {}))
    watcher.look(0.0)
    sent.clear()

    blocked = ok(capsys, world, "land", "checks", SLUG, "--repair-limit")
    why = "two builders could not repair the checks"
    assert why in blocked["say"]
    assert world.record()["task"]["hold"]["why"] == why
    assert ok(capsys, world, "land", "next", SLUG)["result"]["step"] == "wait"
    assert refused(capsys, world, "land", "checks", SLUG)["code"] == "not-due"
    waits = board.client.get(f"{board.base}/waits")
    assert waits.status_code == 200
    assert why in waits.text
    assert watcher.look(10.0) == 1
    assert [(push.tag, push.url) for push in sent] == [
        (f"lem-blocked:{SLUG}", f"{board.base}/tasks/{SLUG}")
    ]
    assert watcher.look(20.0) == 0

    fix = world.record()["task"]["hold"]["fix"]
    assert f"lem task move {SLUG} ready" in fix
    ok(capsys, world, "task", "move", SLUG, "ready", "--line", "the owner says go on")
    assert world.record()["task"].get("hold") is None
