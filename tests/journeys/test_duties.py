"""The board server's duties across workspaces, as its runner takes them at each tick: the three
seams of `serve.forge_loop` on `main` (a failed look at the forge, a failed duty, a failed prune,
each costing no other duty and no other workspace), and the duties of a real landing on real git
and `LocalForge`: the bookkeeping of a pull request merged or closed on GitHub, and the merge
agent's merge that the server makes, with the count of approved tasks that waited.
"""

import json
import shutil
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import anyio
import pytest
from msgspec.structs import replace

from fakes.forge import LocalForge
from fakes.git import ModelGit
from fakes.ports import fake_ports
from fakes.repo import run_git
from fakes.terminal import FakeTerminal
from journeys.landing.test_checks import committed, criteria_tests, settings
from journeys.landing.test_merge import ROUND, SAFE, moved, owner, read
from journeys.test_skeleton import (
    BRANCH,
    JOURNEY,
    SLUG,
    SUBJECT,
    World,
    command,
    due,
    made,
    upto,
)
from lem.adapters.git_cli import GitCli
from lem.app import wiring
from lem.app.landing import changes, frame, merge, merged
from lem.app.sessions import acts, log
from lem.board.duties import merge_line, runner
from lem.board.duties.memory import MEMORY
from lem.kernel import clock
from lem.kernel.errors import Refusal
from lem.model.landing.merge_asked import Asked
from lem.ports.faults import Unanswered
from lem.ports.terminal import Opening
from lem.records.criterion import CriterionTest
from lem.records.holds import ReleaseHold
from lem.records.landing.merge import MergeIntent
from lem.records.landing.record import Pull
from lem.store import places, steps, tasks

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime

    from lem.app.landing.frame import Context
    from lem.app.landing.merge_called import BeforeCall
    from lem.board.duties.context import Duty
    from lem.ports.forge_facts import MergeMethod, MergeText
    from lem.records.record import Record

type Capsys = pytest.CaptureFixture[str]
LOOK = timedelta(seconds=180)
NAMES = ("forge", "merge", "conflict", "queue", "guard", "prune")


def workspace(folder: Path) -> Path:
    """A checkout with Lem set up and its state folder, as the list names it."""
    (folder / ".git").mkdir(parents=True)
    (folder / ".lem").mkdir()
    places.state_of(folder)
    return folder


def listed(home: Path, *checkouts: Path) -> None:
    """The machine's list of workspaces."""
    (home / "workspaces.json").write_text(json.dumps([str(one) for one in checkouts]))


def recorded(
    monkeypatch: pytest.MonkeyPatch, broken: tuple[str, str] | None = None
) -> list[tuple[str, str]]:
    """Each duty's tick, by workspace name and duty; the duty `broken` names raises in its
    workspace."""
    calls: list[tuple[str, str]] = []
    for name in NAMES:
        module = __import__(f"lem.board.duties.{name}", fromlist=["tick"])
        monkeypatch.setattr(module, "tick", ticking(calls, name, broken))
    return calls


def ticking(
    calls: list[tuple[str, str]], name: str, broken: tuple[str, str] | None
) -> Callable[[Duty], None]:
    def tick(duty: Duty) -> None:
        calls.append((duty.name, name))
        if broken == (duty.name, name):
            raise RuntimeError(f"the {name} of {duty.name} broke")

    return tick


@pytest.fixture
def spaces(
    tmp_path: Path, own_home: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path]:
    """Two workspaces on the list, `alpha` and `beta`, on fakes."""
    alpha = workspace(tmp_path / "alpha")
    beta = workspace(tmp_path / "beta")
    listed(own_home, alpha, beta)
    git = ModelGit(checkout=alpha)
    ports = fake_ports(git, LocalForge(remote=git))
    monkeypatch.setattr(wiring, "bound", lambda place: ports)
    return alpha, beta


def every(workspace_name: str) -> list[tuple[str, str]]:
    return [(workspace_name, name) for name in NAMES]


def test_a_failed_look_at_the_forge_is_its_boards_problem_and_every_other_duty_still_runs(
    spaces: tuple[Path, Path],
    own_home: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: Capsys,
) -> None:
    alpha, beta = spaces
    calls = recorded(monkeypatch, ("alpha", "forge"))
    runner.tick(own_home, clock.now())
    assert calls == every("alpha") + every("beta")
    said = "the board's look at GitHub failed: RuntimeError: the forge of alpha broke"
    assert MEMORY.problems_of(alpha) == (said,)
    assert MEMORY.problems_of(beta) == ()
    assert f"lem serve: alpha: {said}" in capsys.readouterr().err
    calls.clear()
    monkeypatch.undo()
    recorded(monkeypatch)
    runner.tick(own_home, clock.now())
    assert MEMORY.problems_of(alpha) == ()


def test_a_failed_duty_is_its_boards_problem_and_its_prune_and_the_next_workspace_still_run(
    spaces: tuple[Path, Path], own_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    alpha, beta = spaces
    calls = recorded(monkeypatch, ("alpha", "guard"))
    runner.tick(own_home, clock.now())
    assert calls == every("alpha") + every("beta")
    assert MEMORY.problems_of(alpha) == (
        "the board's duty guard failed: RuntimeError: the guard of alpha broke",
    )
    assert MEMORY.problems_of(beta) == ()


def test_a_failed_prune_is_one_line_in_the_servers_log_and_the_next_workspace_still_runs(
    spaces: tuple[Path, Path],
    own_home: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: Capsys,
) -> None:
    alpha = spaces[0]
    calls = recorded(monkeypatch, ("alpha", "prune"))
    runner.tick(own_home, clock.now())
    assert calls == every("alpha") + every("beta")
    assert MEMORY.problems_of(alpha) == ()
    said = capsys.readouterr().err.splitlines()
    assert said == [
        "lem serve: alpha: lem prune failed: RuntimeError: the prune of alpha broke"
    ]


def test_a_workspace_of_example_tasks_and_one_no_longer_set_up_owe_nothing(
    spaces: tuple[Path, Path], own_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    alpha, beta = spaces
    (alpha / ".lem" / "state" / "demo").write_text("the afternoon\n")
    shutil.rmtree(beta / ".lem")
    calls = recorded(monkeypatch)
    runner.tick(own_home, clock.now())
    assert calls == []


def test_the_duties_run_every_twenty_seconds_off_the_event_loop_until_the_server_stops(
    own_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert runner.TICK == 20
    ticks: list[Path] = []
    stopping = anyio.Event()

    def ticked(home: Path) -> None:
        ticks.append(home)
        if len(ticks) == 2:
            stopping.set()

    monkeypatch.setattr(runner, "tick", ticked)
    monkeypatch.setattr(runner, "TICK", 0.01)
    anyio.run(runner.loop, own_home, stopping)
    assert ticks == [own_home, own_home]


def github(_git: GitCli, _where: Path) -> str:
    """Origin's address as the server reads it: on GitHub, whatever folder serves as origin."""
    return "git@github.com:owner/project.git"


def served(world: World, home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The world's checkout on the machine's list, its origin on GitHub."""
    listed(home, world.checkout)
    monkeypatch.setattr(GitCli, "origin_url", github)


def ticked(world: World, home: Path, now: datetime) -> None:
    """Run a tick and wait for its merge to finish."""
    runner.tick(home, now)
    for run in MEMORY.of(world.checkout).merging.values():
        run.join()


def test_a_stale_server_request_leaves_the_newly_reviewed_tip_untouched(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: Capsys,
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    before = world.record()
    current = before["landing"]["proposed"]["tip"]
    stale = "a" * 40
    assert stale != current

    with pytest.raises(Refusal) as caught:
        merge.run(
            world.checkout,
            SLUG,
            Asked(by="merger", via="server", tip=stale, subject=SUBJECT),
        )

    assert caught.value.code == "tip"
    assert world.record() == before
    assert world.forge.merge_calls == []


def test_the_server_reports_the_queue_and_reconciles_a_confirmed_dequeue(
    tmp_path: Path,
    own_home: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: Capsys,
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    served(world, own_home, monkeypatch)
    world.forge.queue = True
    now = clock.now()
    ticked(world, own_home, now)
    assert world.record()["landing"]["accepted"]["queued"] == "the merge queue"
    queued = MEMORY.of(world.checkout).said[SLUG]

    world.forge.dequeue(1, "a required check failed in the queue")
    ticked(world, own_home, now + LOOK)

    landing = world.record()["landing"]
    assert "accepted" not in landing
    assert landing["refused"]["line"] == "a required check failed in the queue"
    assert "the merge queue" in queued
    assert not queued.startswith("Merged:")
    assert len(world.forge.merge_calls) == 1


def test_the_server_finishes_a_confirmed_merge_after_a_lost_reply(
    tmp_path: Path, own_home: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    served(world, own_home, monkeypatch)
    call = world.forge.merge

    def lost(
        number: int, expected_head: str, method: MergeMethod, text: MergeText
    ) -> None:
        call(number, expected_head, method, text)
        raise Unanswered("gh", "connection reset after the merge")

    monkeypatch.setattr(world.forge, "merge", lost)
    now = clock.now()
    ticked(world, own_home, now)
    assert world.record()["landing"]["intent"]["by"] == "merger"

    ticked(world, own_home, now + LOOK)

    assert world.record()["task"]["status"] == "landed"
    landing = world.record()["landing"]
    assert "intent" not in landing
    assert (landing["merged"]["by"], landing["merged"]["via"]) == ("merger", "server")
    assert len(world.forge.merge_calls) == 1


def test_the_board_shows_the_recorded_end_of_a_queued_merge(
    tmp_path: Path, own_home: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    served(world, own_home, monkeypatch)
    world.forge.queue = True
    now = clock.now()
    ticked(world, own_home, now)
    kept = MEMORY.of(world.checkout)
    assert kept.said[SLUG].startswith("Queued:")

    world.forge.settle(1)
    ticked(world, own_home, now + LOOK)

    assert world.record()["task"]["status"] == "landed"
    assert kept.said[SLUG].startswith(f"Merged: {SLUG} is on the base.")
    assert len(world.forge.merge_calls) == 1


def test_bookkeeping_follows_a_server_merge_before_the_next_forge_poll(
    tmp_path: Path,
    own_home: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: Capsys,
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    served(world, own_home, monkeypatch)
    now = clock.now()
    ticked(world, own_home, now)
    kept = MEMORY.of(world.checkout)
    thread = kept.merging[SLUG]
    assert kept.said[SLUG].startswith(f"Merged: {SLUG} is on the base.")

    ticked(world, own_home, now + timedelta(seconds=1))

    assert world.record()["task"]["status"] == "landed"
    assert kept.merging[SLUG] is thread
    assert kept.said[SLUG].startswith(f"Merged: {SLUG} is on the base.")
    assert len(world.forge.merge_calls) == 1


def test_merge_line_records_only_forge_calls_and_counts_current_eligible_approvals(
    tmp_path: Path,
    own_home: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: Capsys,
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    served(world, own_home, monkeypatch)
    state = world.task_folder.parents[1]
    now = clock.now()
    with steps.step(state, SLUG, "merge-review", now):
        ticked(world, own_home, now)
    refused_lines = merge_line.read(state)

    found = tasks.read(state, SLUG)
    hold = ReleaseHold(began="0.1.0", running="0.3.0", say="old release", since=now)
    tasks.create(
        state, replace(found, task=replace(found.task, slug="held", hold=hold))
    )
    tasks.create(state, replace(found, task=replace(found.task, slug="was-waiting")))
    tasks.create(state, replace(found, task=replace(found.task, slug="still-waiting")))
    decide = merge.locked

    def finish_another_before_the_call(
        context: Context, asked: Asked, before_call: BeforeCall | None
    ) -> object:
        other = tasks.read(state, "was-waiting")
        tasks.update(
            state,
            "was-waiting",
            lambda record: replace(record, task=replace(record.task, status="landed")),
            other.revision,
        )
        return decide(context, asked, before_call)

    monkeypatch.setattr(merge, "locked", finish_another_before_the_call)
    kept = MEMORY.of(world.checkout)
    kept.failed.clear()
    with (
        steps.step(state, "was-waiting", "merged", now),
        steps.step(state, "still-waiting", "merge-review", now),
    ):
        ticked(world, own_home, now + timedelta(seconds=1))

    assert refused_lines == ()
    assert [(one.task, one.waiting, one.behind) for one in merge_line.read(state)] == [
        (SLUG, 1, ("still-waiting",))
    ]


@pytest.mark.parametrize("blocked", ["lock-file", "lock-folder"])
def test_an_unopenable_merge_lock_shows_the_repair_and_waits_from_failure_time(
    tmp_path: Path,
    own_home: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: Capsys,
    blocked: str,
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    served(world, own_home, monkeypatch)
    new_base = moved(world)
    approve_on_board(world)
    land_again(capsys, world)
    landing = world.record()["landing"]
    assert landing["proposed"]["owner_merge"]["state"] == "stands"
    assert landing["standing"]["tip"] == landing["proposed"]["tip"]
    assert landing["checked"]["base"] == new_base
    assert "The review carried over the rebase." in world.forge.bodies[1]
    now = clock.now()
    failed_at = now + timedelta(minutes=2)
    monkeypatch.setattr(clock, "now", lambda: failed_at)
    path = world.task_folder.parents[1] / "locks" / "merge.lock"
    if blocked == "lock-file":
        path.unlink()
        path.mkdir(parents=True)
    else:
        path = path.parent
        if path.is_dir():
            path.rename(path.with_name("locks-before-test"))
        path.write_text("this path is a file")

    ticked(world, own_home, now)

    kept = MEMORY.of(world.checkout)
    line = kept.said[SLUG]
    assert str(path) in line and "remove" in line and "lem land merge" in line
    assert tuple(kept.failed.values()) == (failed_at,)
    assert world.forge.merge_calls == []
    assert world.record()["landing"]["standing"] == landing["standing"]


def test_the_server_carries_out_the_owners_merge_after_a_safe_read(
    tmp_path: Path,
    own_home: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: Capsys,
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    served(world, own_home, monkeypatch)
    old = world.record()["landing"]["checked"]
    new_base = moved(world)
    assert read(capsys, world, SAFE)["ok"] is True
    approve_on_board(world)
    now = clock.now()
    ticked(world, own_home, now)
    assert world.forge.merge_calls == []
    assert due(capsys, world) == "start"
    land_again(capsys, world)
    landing = world.record()["landing"]
    checked = landing["checked"]
    assert checked["tip"] != old["tip"]
    assert checked["tip"] == landing["proposed"]["tip"]
    assert checked["base"] == new_base
    assert run_git(world.worktree, "rev-parse", "HEAD^") == new_base
    assert checked["outcome"] == "passed"
    assert landing["standing"]["tip"] == checked["tip"]
    assert landing["based"]["reviewed"] == old["tip"]
    ticked(world, own_home, now + timedelta(seconds=1))
    merged = world.record()["landing"]["merged"]
    assert (merged["by"], merged["via"]) == ("owner", "server")
    assert merged["base_checked"] == merged["base_merged"] == new_base
    assert len(world.forge.merge_calls) == 1


def approve_on_board(world: World) -> None:
    """The board's request to approve the tip the owner saw."""
    tip = world.record()["landing"]["proposed"]["tip"]
    with pytest.raises(Refusal) as refused:
        merge.run(
            world.checkout,
            SLUG,
            Asked(by="owner", via="board", tip=tip, subject=SUBJECT),
        )
    assert refused.value.code == "base"
    assert world.record()["landing"]["standing"]["by_act"] == "board"


def land_again(capsys: Capsys, world: World) -> None:
    """Take each due landing step through the next merge."""
    for verb, step in JOURNEY:
        if verb == "merge":
            return
        if verb is not None and due(capsys, world) == verb:
            answer = step(capsys, world)
            assert answer["ok"] is True, answer


def other_destination(world: World, original: Record) -> str:
    """A second task on a branch that still points to the checked base and can merge now."""
    slug, branch, destination = "other-task", "docs/other-task", "release"
    landing = original.landing
    assert (
        landing is not None
        and landing.started is not None
        and landing.proposed is not None
    )
    tip, base = landing.proposed.tip, landing.proposed.base
    run_git(world.checkout, "push", "origin", f"{base}:refs/heads/{destination}")
    worktree = world.worktree.with_name(slug)
    run_git(world.checkout, "worktree", "add", "-b", branch, str(worktree), tip)
    run_git(worktree, "push", "origin", branch)
    pull = world.forge.open_pull(branch, destination, SUBJECT, "A second task")
    started = replace(landing.started, branch=branch, base_ref=destination)
    other = replace(
        landing,
        started=started,
        pull=Pull(number=pull.number, url=pull.url, title=pull.title),
    )
    task = replace(original.task, slug=slug, branch=branch)
    tasks.create(
        world.task_folder.parents[1], replace(original, task=task, landing=other)
    )
    return slug


@pytest.mark.parametrize("criterion", [False, True], ids=["command", "criterion"])
def test_a_red_rebase_leaves_the_line_until_its_builder_repairs_it(
    tmp_path: Path,
    own_home: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: Capsys,
    *,
    criterion: bool,
) -> None:
    world = made(tmp_path, monkeypatch)
    condition = (
        "if test -f LATER.md && grep -q receive README.md; then test -f compatible; fi"
    )
    if criterion:
        upto(capsys, world, "checks")
        criteria_tests(
            world, CriterionTest(command=f"grep -q receive README.md && {condition}")
        )
        land_again(capsys, world)
    else:
        settings(world, json.dumps([condition]))
        upto(capsys, world, "merge")
    state = world.task_folder.parents[1]
    before = tasks.read(state, SLUG)
    served(world, own_home, monkeypatch)
    new_base = moved(world, "LATER.md")
    approve_on_board(world)
    now = clock.now()
    ticked(world, own_home, now)
    for verb in ("start", "base"):
        assert command("land", verb, "SLUG")(capsys, world)["ok"] is True
    answer = command("land", "checks", "SLUG")(capsys, world)
    assert answer["refusal"]["code"] == ("criteria" if criterion else "red")
    record = world.record()
    landing = record["landing"]
    assert landing["checked"]["base"] == new_base
    assert landing["checked"]["outcome"] == ("refused" if criterion else "red")
    assert landing["standing"]["tip"] == landing["proposed"]["tip"]
    assert "a builder repairs it" in record["journal"][-1]["say"]
    assert record["task"].get("hold") is None
    other = other_destination(world, before)
    ticked(world, own_home, now + timedelta(seconds=1))
    assert [number for number, _ in world.forge.merge_calls] == [2]
    other_landing = tasks.read(state, other).landing
    assert other_landing is not None and other_landing.merged is not None
    assert [(one.task, one.waiting, one.behind) for one in merge_line.read(state)] == [
        (other, 0, ())
    ]

    committed(world, "compatible", "the task also works with the new base\n")
    land_again(capsys, world)
    landing = world.record()["landing"]
    assert landing["checked"]["outcome"] == "passed"
    assert landing["standing"]["tip"] == landing["proposed"]["tip"]
    ticked(world, own_home, now + timedelta(seconds=2))
    assert world.record()["landing"]["merged"]["by"] == "owner"
    assert [number for number, _ in world.forge.merge_calls] == [2, 1]


def test_the_server_merges_the_reviewed_new_tip_after_a_new_round(
    tmp_path: Path,
    own_home: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: Capsys,
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    served(world, own_home, monkeypatch)
    old = world.record()["landing"]["proposed"]["tip"]
    moved(world)
    assert read(capsys, world, ROUND)["ok"] is True
    assert owner(capsys, world)["refusal"]["code"] == "base"
    now = clock.now()
    ticked(world, own_home, now)
    assert world.forge.merge_calls == []
    land_again(capsys, world)
    landing = world.record()["landing"]
    tip = landing["proposed"]["tip"]
    assert tip != old
    assert landing["proposed"]["owner_merge"]["state"] == "stands"
    assert landing["standing"]["tip"] == tip
    ticked(world, own_home, now + timedelta(seconds=1))
    merged = world.record()["landing"]["merged"]
    assert (merged["by"], merged["via"], merged["merged_head"]) == (
        "owner",
        "server",
        tip,
    )
    assert len(world.forge.merge_calls) == 1


def test_a_ready_merge_does_not_delay_the_wake_for_a_second_base_move(
    tmp_path: Path, own_home: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    original = tasks.read(world.task_folder.parents[1], SLUG)
    moved(world)
    approve_on_board(world)
    land_again(capsys, world)
    landing = world.record()["landing"]
    assert landing["standing"]["tip"] == landing["proposed"]["tip"]
    assert "refused" not in landing
    moved(world, "AGAIN.md")
    other = other_destination(world, original)
    run_git(world.checkout, "fetch", "origin")
    served(world, own_home, monkeypatch)
    now = clock.now()
    terminal = frame.bound(places.workspace(world.checkout)).terminal
    opening = Opening(
        name=SLUG, cwd=str(world.checkout), command=("claude",), workspace="test"
    )
    session = terminal.open(opening)
    log.reached(
        world.task_folder,
        acts.Open(
            at=now,
            session=session,
            name=SLUG,
            phase="fast",
            why="new",
            workspace="test",
        ),
    )

    ticked(world, own_home, now)
    ticked(world, own_home, now + timedelta(seconds=1))

    assert [number for number, _ in world.forge.merge_calls] == [2]
    assert tasks.read(world.task_folder.parents[1], other).task.status == "landed"
    observed = [
        act for act in log.read(world.task_folder) if isinstance(act, acts.Wake)
    ]
    assert [(act.why, act.head) for act in observed] == [
        ("refused", landing["proposed"]["tip"])
    ]
    assert due(capsys, world) == "start"


def test_the_ledger_names_journeys_for_the_new_tip_safe_read_and_merge_result() -> None:
    path = Path(__file__).parents[1] / "ledger" / "fates" / "board-duties.tsv"
    rows = {
        line.split("\t")[0]: line.split("\t")[2]
        for line in path.read_text().splitlines()[1:]
    }
    proofs = {
        "duty:publish-merge-result": test_the_server_reports_the_queue_and_reconciles_a_confirmed_dequeue,
        "Duties.test_after_a_moved_base_the_session_lands_it_again_and_the_server_merges_the_new_tip": test_the_server_merges_the_reviewed_new_tip_after_a_new_round,
        "MovedBaseRead.test_the_owners_merge_a_moved_base_refused_goes_through_on_a_safe_read": test_the_server_carries_out_the_owners_merge_after_a_safe_read,
    }
    for suffix, test in proofs.items():
        (proof,) = (proof for key, proof in rows.items() if key.endswith(suffix))
        assert proof == f"journeys.test_duties.{test.__name__}"


def test_a_pull_request_merged_on_github_gets_its_bookkeeping_and_the_task_lands(
    tmp_path: Path, own_home: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    served(world, own_home, monkeypatch)
    world.forge.outside_merge(1)
    runner.tick(own_home, clock.now())
    assert world.record()["task"]["status"] == "landed"
    assert world.record()["landing"]["merged"]["via"] == "github"
    assert len(world.forge.merge_calls) == 0
    assert merge_line.read(world.checkout / ".lem" / "state") == ()


def test_the_board_records_the_forge_merge_and_only_wakes_the_live_task_session(
    tmp_path: Path, own_home: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    served(world, own_home, monkeypatch)
    terminal = frame.bound(places.workspace(world.checkout)).terminal
    assert isinstance(terminal, FakeTerminal)
    opening = Opening(
        name=SLUG, cwd=str(world.checkout), command=("claude",), workspace="test"
    )
    session = terminal.open(opening)
    owner_session = terminal.open(replace(opening, name="owner"))
    terminal.select(owner_session)
    now = clock.now()
    log.reached(
        world.task_folder,
        acts.Open(
            at=now,
            session=session,
            name=SLUG,
            phase="land",
            why="new",
            workspace="test",
        ),
    )
    panes = terminal.sessions()

    world.forge.outside_merge(1)
    runner.tick(own_home, now)
    runner.tick(own_home, now + LOOK)

    assert world.record()["task"]["status"] == "landed"
    assert world.record()["landing"]["merged"]["via"] == "github"
    assert world.forge.merge_calls == []
    assert terminal.told == [(session, f"lem: {SLUG} merged")]
    assert terminal.sessions() == panes
    assert len(terminal.openings) == 2
    assert terminal.closed == []


def test_a_pull_request_closed_on_github_drops_the_task_and_its_branch_keeps_its_commits(
    tmp_path: Path, own_home: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    served(world, own_home, monkeypatch)
    world.forge.close(1)
    runner.tick(own_home, clock.now())
    assert world.record()["task"]["status"] == "dropped"
    assert run_git(world.checkout, "rev-parse", "--verify", "--quiet", BRANCH)
    assert len(world.forge.merge_calls) == 0


def test_the_server_makes_the_merge_agents_merge_and_records_the_approved_tasks_waiting(
    tmp_path: Path, own_home: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    served(world, own_home, monkeypatch)
    now = clock.now()
    runner.tick(own_home, now)
    for run in MEMORY.of(world.checkout).merging.values():
        run.join()
    assert [number for number, _ in world.forge.merge_calls] == [1]
    assert world.record()["landing"]["merged"]["by"] == "merger"
    assert world.record()["landing"]["merged"]["via"] == "server"
    lines = merge_line.read(world.checkout / ".lem" / "state")
    assert [(one.by, one.waiting, one.behind) for one in lines] == [("merger", 0, ())]
    runner.tick(own_home, now + LOOK)
    assert world.record()["task"]["status"] == "landed"
    assert len(world.forge.merge_calls) == 1
    assert SUBJECT in run_git(world.repo.origin, "log", "-1", "--format=%s", "main")


def test_the_landing_refuses_an_old_release_before_the_forge_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    path = world.task_folder / tasks.RECORD
    current = tasks.read(world.task_folder.parents[1], SLUG)
    path.write_bytes(tasks.encode(replace(current, release="0.2.0")))

    with pytest.raises(Refusal) as caught:
        merge.run(
            world.checkout,
            SLUG,
            Asked(by="merger", via="server", subject=SUBJECT),
        )

    assert caught.value.code == "release"
    assert world.forge.merge_calls == []

    world.forge.outside_merge(1)
    merged.run(world.checkout, SLUG)

    assert world.record()["task"]["status"] == "landed"


def test_the_server_recovers_a_lost_queue_reply_without_a_second_merge_call(
    tmp_path: Path, own_home: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    served(world, own_home, monkeypatch)
    world.forge.queue = True
    call = world.forge.merge

    def lost(
        number: int, expected_head: str, method: MergeMethod, text: MergeText
    ) -> None:
        call(number, expected_head, method, text)
        raise Unanswered("gh", "connection reset after the queue took the merge")

    monkeypatch.setattr(world.forge, "merge", lost)
    now = clock.now()
    ticked(world, own_home, now)
    assert "intent" in world.record()["landing"]

    ticked(world, own_home, now + LOOK)

    landing = world.record()["landing"]
    assert "intent" not in landing
    assert landing["accepted"]["queued"] == "the merge queue"
    assert MEMORY.of(world.checkout).said[SLUG].startswith("Queued:")
    assert len(world.forge.merge_calls) == 1


def test_an_old_queue_removal_does_not_answer_a_later_call(
    tmp_path: Path, own_home: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    served(world, own_home, monkeypatch)
    state = world.task_folder.parents[1]
    current = tasks.read(state, SLUG)
    now = clock.now()
    world.forge.dequeue(1, "a check failed before the new call")
    assert current.landing is not None and current.landing.proposed is not None
    tip = current.landing.proposed.tip
    intent = MergeIntent(
        tip=tip, by="merger", via="server", at=now + timedelta(seconds=1)
    )
    tasks.update(
        state, SLUG, lambda one: changes.landing(one, intent=intent), current.revision
    )

    # The explicit landing entry reconciles the intent without permission for another call.
    with pytest.raises(Refusal) as caught:
        merge.run(world.checkout, SLUG, Asked(by="merger", via="server", tip=tip))

    assert caught.value.code == "intent"
    assert world.record()["landing"]["intent"]["tip"] == tip
    assert world.forge.merge_calls == []


def test_the_wrong_base_remedy_survives_a_bookkeeping_retry(
    tmp_path: Path, own_home: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge")
    served(world, own_home, monkeypatch)
    world.repo.outside_commit("release", {"RELEASE.md": b"a release\n"})
    world.forge.retarget(1, "release")
    world.forge.outside_merge(1)
    now = clock.now()
    ticked(world, own_home, now)
    kept = MEMORY.of(world.checkout)
    problem = f"merged:{SLUG}"
    assert "drops the task" in kept.problems[problem]

    ticked(world, own_home, now + 2 * LOOK)

    assert "drops the task" in kept.problems[problem]
    assert "brings the change onto main" in kept.problems[problem]
    assert world.record()["task"]["status"] == "open"
