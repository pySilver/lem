"""The board server's duties across workspaces, as its runner takes them at each tick: the three
seams of `serve.forge_loop` on `main` (a failed look at the forge, a failed duty, a failed prune,
each costing no other duty and no other workspace), and the duties of a real landing on real git
and `LocalForge`: the bookkeeping of a pull request merged or closed on GitHub, and the merge
agent's merge that the server makes, with the count of approved tasks that waited.
"""

import json
import shutil
from datetime import timedelta
from typing import TYPE_CHECKING

import anyio
import pytest

from fakes.forge import LocalForge
from fakes.git import ModelGit
from fakes.ports import fake_ports
from fakes.repo import run_git
from journeys.test_skeleton import BRANCH, SUBJECT, World, made, upto
from lem.adapters.git_cli import GitCli
from lem.app import wiring
from lem.board.duties import merge_line, runner
from lem.board.duties.memory import MEMORY
from lem.kernel import clock
from lem.store import places

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from lem.board.duties.context import Duty

type Capsys = pytest.CaptureFixture[str]
LOOK = timedelta(seconds=180)
NAMES = ("forge", "merge", "conflict", "queue", "guard", "notify", "prune")


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
