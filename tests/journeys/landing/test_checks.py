"""The checks and the polish pass on a real repository: a fast-track task of the walking skeleton
(`tests/journeys/test_skeleton.py`) taken to the step `checks`, then each path the step
`land-checks` proves (`landing.md` E and F; `tests/lem-serial.sh` on `main`).

Every `lem` runs in this process through the tree (`lem.cli.lazy.main`), with the skeleton's
ports, but where a stop needs a process of its own: then a runner script binds the same ports
in a child, and the test ends it in a `finally`. The machine's start number is set high, so that
the load of a busy machine never holds a case at the gate it does not test.
"""

import fcntl
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from msgspec.structs import replace

from fakes.repo import run_git
from journeys.test_skeleton import SLUG, World, lem, made, upto
from lem.app.landing import checks_criteria
from lem.kernel import folders
from lem.records.criterion import CriterionTest
from lem.records.work import Plan
from lem.store import places, tasks

if TYPE_CHECKING:
    from collections.abc import Iterator

    from lem.records.record import Record

type Envelope = dict[str, Any]
TESTS = Path(__file__).resolve().parents[2]
# How long a case waits for a child to reach a point, in seconds: a child starts Python, git
# and a command on a machine other builders load (unmeasured estimate, with room).
REACH = 60.0


def machine(start: str) -> None:
    """This machine's start number of the load gate, in the test's own home."""
    home = folders.home_for_writing(os.environ)
    (home / "machine.toml").write_text(f"[load]\nstart = {start}\n")


def settings(world: World, commands: str, serial: str = "[]") -> None:
    """The main checkout's checks, as the main checkout's file says them now."""
    path = world.checkout / ".lem" / "settings.toml"
    head = path.read_text().split("[checks]")[0]
    path.write_text(f"{head}[checks]\ncommands = {commands}\nserial = {serial}\n")


@pytest.fixture
def world(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> World:
    """The skeleton's task, up to the step `checks`, on a machine whose gate lets it start."""
    machine("1000")
    made_world = made(tmp_path, monkeypatch)
    upto(capsys, made_world, "checks")
    return made_world


def checks(capsys: pytest.CaptureFixture[str], world: World, *words: str) -> Envelope:
    """`lem land checks SLUG WORDS` in the main checkout."""
    return lem(capsys, world.checkout, "land", "checks", SLUG, *words)


def due(capsys: pytest.CaptureFixture[str], world: World) -> str:
    """The step `lem land next` names."""
    return str(lem(capsys, world.checkout, "land", "next", SLUG)["result"]["step"])


def record_of(world: World) -> Envelope:
    """The task's record, as its file says it."""
    return world.record()


def committed(world: World, name: str, body: str, message: str = "a change") -> None:
    """A commit of the builder in the task's worktree."""
    path = world.worktree / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    run_git(world.worktree, "add", "--all")
    run_git(world.worktree, "commit", "--quiet", "--message", message)


def lock_path(world: World) -> Path:
    return world.checkout / ".lem" / "state" / "locks" / "serial.lock"


# Whether the serial lock is held: the probe a serial command runs, which prints its answer.
HELD = (
    "import fcntl, sys\n"
    "stream = open(sys.argv[1], 'a+')\n"
    "try:\n"
    "    fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)\n"
    "    print('free')\n"
    "except BlockingIOError:\n"
    "    print('held')\n"
)


def test_the_checks_run_each_serial_command_after_the_commands_under_the_one_lock(
    world: World, capsys: pytest.CaptureFixture[str]
) -> None:
    probe = world.folder / "held.py"
    probe.write_text(HELD)
    serial = f'["{sys.executable} -I {probe} {lock_path(world)}"]'
    settings(world, '["test -f README.md"]', serial)
    places.locks_folder(world.checkout / ".lem" / "state")
    builder = lock_path(world).open("a+")
    fcntl.flock(builder, fcntl.LOCK_EX)
    let_go = threading.Timer(2.0, builder.close)
    let_go.start()
    try:
        envelope = checks(capsys, world)
    finally:
        let_go.cancel()
        builder.close()
    assert envelope["ok"] is True, envelope
    outcomes = record_of(world)["landing"]["checked"]["outcomes"]
    assert [(one.get("serial", False), one["passed"]) for one in outcomes] == [
        (False, True),
        (True, True),
    ]
    log = (world.task_folder / outcomes[1]["output"]).read_text()
    assert "another serial test holds the lock" in log
    assert outcomes[1]["last"] == "held"
    assert due(capsys, world) == "read"


def test_a_red_command_leaves_the_serial_commands_out(
    world: World, capsys: pytest.CaptureFixture[str]
) -> None:
    marker = world.folder / "serial-ran"
    settings(world, '["test -f README.md", "false"]', f'["touch {marker}"]')
    refused = checks(capsys, world)
    assert refused["refusal"]["code"] == "red"
    assert "the checks are red on 1 command(s): false" in refused["refusal"]["why"]
    assert not marker.exists()
    found = record_of(world)
    assert found["landing"]["checked"]["outcome"] == "red"
    end = found["journal"][-1]
    assert (end["kind"], end["outcome"]) == ("check-end", "red")
    assert (
        end["say"]
        == f"{SLUG}: the checks are red on false; a builder repairs it, nothing for you"
    )
    assert due(capsys, world) == "checks"


def test_the_checks_remove_what_their_commands_leave(
    world: World, capsys: pytest.CaptureFixture[str]
) -> None:
    exclude = world.checkout / ".git" / "info" / "exclude"
    exclude.write_text("__pycache__/\n.venv/\n")
    stale = world.worktree / "pkg" / "__pycache__"
    stale.mkdir(parents=True)
    (stale / "x.pyc").write_bytes(b"\0")
    (world.worktree / ".venv" / "__pycache__").mkdir(parents=True)
    settings(world, '["mkdir -p out/deep && touch out/deep/left.txt left.txt"]')
    assert checks(capsys, world)["ok"] is True
    removed = record_of(world)["landing"]["checked"]["removed"]
    assert removed["bytecode"] == ["pkg/__pycache__/"]
    assert removed["untracked"] == ["left.txt", "out/deep/left.txt"]
    assert (world.worktree / ".venv" / "__pycache__").is_dir()
    assert run_git(world.worktree, "status", "--porcelain") == ""


@pytest.mark.parametrize(
    ("command", "said"),
    [
        ("echo more >> README.md", "changed what git tracks"),
        (
            "git -c user.name=t -c user.email=t@t commit -q --allow-empty -m x",
            "made a commit",
        ),
    ],
    ids=["a tracked file", "a commit"],
)
def test_a_command_that_changes_the_tree_it_judges_is_refused(
    world: World, capsys: pytest.CaptureFixture[str], command: str, said: str
) -> None:
    settings(world, f'["{command}"]')
    refused = checks(capsys, world)["refusal"]
    assert refused["code"] == "tracked-change"
    assert said in refused["why"]
    assert record_of(world)["landing"]["checked"]["outcome"] == "refused"


def test_a_fast_track_change_that_lowers_the_bar_takes_the_standard_track(
    world: World, capsys: pytest.CaptureFixture[str]
) -> None:
    committed(world, "calc.py", "import os  # " + "noqa\n")
    assert due(capsys, world) == "checks"
    refused = checks(capsys, world)["refusal"]
    assert refused["code"] == "bar"
    assert "calc.py" in refused["why"]
    found = record_of(world)
    assert found["task"]["status"] == "shaping"
    assert found["task"]["shape"]["track"] == "full"
    assert (found["task"]["hold"]["kind"], found["task"]["hold"]["on"]) == (
        "owner",
        "interview",
    )
    assert found["landing"]["checked"]["lowered"][0]["path"] == "calc.py"
    assert found["journal"][-1]["line"].startswith(f"{SLUG} lowers the bar")


# A run that waits at the gate, and one whose command runs, each stopped by `--stop` from
# another process, as a session or the board does.

RUNNER = """
import sys
from pathlib import Path
sys.path[:0] = [sys.argv[1]]
from fakes.forge import LocalForge
from fakes.harness import FakeHarness
from fakes.outside import FakeJudge, FakeTracker, RecordingNotifier
from fakes.repo import RealRepo, git_env
from fakes.terminal import FakeTerminal
from lem.adapters import git_cli
from lem.app import wiring
from lem.cli import lazy
from lem.ports.place import Place
folder, checkout = Path(sys.argv[2]), Path(sys.argv[3])
repo = RealRepo(origin=folder / "origin.git", checkout=checkout, teammate=folder / "teammate", branch="main")
place = Place(checkout=checkout, home=folder / "home", environ=git_env())
ports = wiring.Ports(git=git_cli.bind(place), forge=LocalForge(remote=repo), terminal=FakeTerminal(), harness=FakeHarness(), tracker=FakeTracker(), notifier=RecordingNotifier(), judge=FakeJudge())
wiring.bound = lambda place: ports
sys.exit(lazy.main(["--repo", str(checkout), "land", "checks", sys.argv[4]]))
"""


@pytest.fixture
def child(world: World) -> Iterator[list[subprocess.Popen[str]]]:
    """The children a case starts, each ended when the case ends."""
    started: list[subprocess.Popen[str]] = []
    yield started
    for proc in started:
        if proc.poll() is None:
            proc.kill()
        proc.communicate(timeout=REACH)


def running(
    world: World, started: list[subprocess.Popen[str]]
) -> subprocess.Popen[str]:
    """`lem land checks SLUG` in a child of its own, with the skeleton's ports."""
    argv = [
        sys.executable,
        "-I",
        "-B",
        "-c",
        RUNNER,
        str(TESTS),
        str(world.repo.checkout.parent),
        str(world.checkout),
        SLUG,
    ]
    proc = subprocess.Popen(
        argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    started.append(proc)
    return proc


def reached(look: object, what: str) -> None:
    """Wait until `look()` is true."""
    deadline = time.monotonic() + REACH
    while time.monotonic() < deadline:
        if callable(look) and look():
            return
        time.sleep(0.2)
    raise AssertionError(f"the child did not reach {what} in {REACH:g} s")


def test_status_names_a_run_that_waits_and_a_stop_there_ends_it_before_its_first_command(
    world: World, capsys: pytest.CaptureFixture[str], child: list[subprocess.Popen[str]]
) -> None:
    machine("0.001")
    proc = running(world, child)

    def waits() -> bool:
        found = checks(capsys, world, "--status")["result"]
        return bool(found["running"] and found.get("waits"))

    reached(waits, "the gate")
    status = checks(capsys, world, "--status")["result"]
    assert status["waits"]["say"] == (
        f"{SLUG}: the checks wait for the load: {status['waits']['wait']['load']:g}, they "
        "start below 0.001"
    )
    stopped = checks(capsys, world, "--stop")["result"]
    assert (stopped["stopped"], stopped["pid"]) == (True, proc.pid)
    out, _ = proc.communicate(timeout=REACH)
    assert proc.returncode == 1
    assert "stopped before their first command" in out
    assert stopped["ended"]["result"] == "stopped"
    after = checks(capsys, world, "--status")["result"]
    assert after["running"] is False
    assert after["ended"]["resumed"].endswith(
        "stopped; the landing waits for your word"
    )
    assert not list((folders.home_for_writing(os.environ) / "load.line").glob("*.json"))


def test_a_stop_ends_the_command_that_runs_with_what_it_started_and_keeps_the_run_stopped(
    world: World, capsys: pytest.CaptureFixture[str], child: list[subprocess.Popen[str]]
) -> None:
    pid_file = world.folder / "command.pid"
    settings(world, f"[\"sh -c 'echo $$ > {pid_file}; sleep 60'\"]")
    proc = running(world, child)
    reached(lambda: pid_file.is_file() and pid_file.read_text().strip(), "its command")
    status = checks(capsys, world, "--status")["result"]
    assert status["running"] is True
    assert status["seconds"] is not None
    assert "waits" not in status
    assert checks(capsys, world, "--stop")["result"]["stopped"] is True
    out, _ = proc.communicate(timeout=REACH)
    assert proc.returncode == 1
    assert "the checks were stopped" in out
    with pytest.raises(ProcessLookupError):
        os.kill(int(pid_file.read_text()), 0)
    found = record_of(world)
    assert found["landing"]["checked"]["outcome"] == "stopped"
    assert found["journal"][-1]["outcome"] == "stopped"
    assert due(capsys, world) == "checks"
    assert checks(capsys, world, "--stop")["result"]["stopped"] is False


# `lem serial` alone.


def serial(world: World, *words: str, wait: bool = True) -> subprocess.Popen[str]:
    """`lem serial -- WORDS` as a process of its own, as a project's suite starts it."""
    argv = [
        sys.executable,
        "-I",
        "-B",
        "-m",
        "lem",
        "--repo",
        str(world.checkout),
        "serial",
        "--",
        *words,
    ]
    proc = subprocess.Popen(
        argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    if wait:
        proc.communicate(timeout=REACH)
    return proc


def test_serial_passes_the_exit_status_through_runs_one_line_in_the_shell_and_refuses_none(
    world: World, capsys: pytest.CaptureFixture[str]
) -> None:
    assert serial(world, "exit 3").returncode == 3
    assert serial(world, "sh", "-c", "exit 4").returncode == 4
    said = serial(world, "echo one; echo two", wait=False)
    out, _ = said.communicate(timeout=REACH)
    assert out == "one\ntwo\n"
    assert (
        lem(capsys, world.checkout, "serial", "--", " ")["refusal"]["code"]
        == "serial-call"
    )


def test_two_runs_at_one_moment_take_turns_and_the_second_says_who_holds_the_lock(
    world: World, child: list[subprocess.Popen[str]]
) -> None:
    first = serial(world, "sleep 3", wait=False)
    child.append(first)
    places.locks_folder(world.checkout / ".lem" / "state")

    def holds() -> bool:
        with lock_path(world).open("a+") as stream:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return True
        return False

    reached(holds, "the serial lock")
    second = serial(world, "true", wait=False)
    _, err = second.communicate(timeout=REACH)
    assert second.returncode == 0
    assert first.poll() is not None
    assert f"another serial test holds the lock (pid {first.pid}" in err


def test_a_stale_lock_file_of_a_dead_process_does_not_block(
    world: World, child: list[subprocess.Popen[str]]
) -> None:
    places.locks_folder(world.checkout / ".lem" / "state")
    lock_path(world).write_text("pid 99999, since 2026-11-19T10:18Z, in /x: sleep 60")
    started = time.monotonic()
    assert serial(world, "true").returncode == 0
    holder = subprocess.Popen(
        [sys.executable, "-c", HOLD_KILLED, str(lock_path(world))],
        stdout=subprocess.PIPE,
        text=True,
    )
    child.append(holder)
    assert holder.stdout is not None
    assert holder.stdout.readline().strip() == "held"
    holder.send_signal(signal.SIGKILL)
    holder.wait(timeout=REACH)
    assert serial(world, "true").returncode == 0
    assert time.monotonic() - started < REACH


HOLD_KILLED = (
    "import fcntl, sys, time\n"
    "stream = open(sys.argv[1], 'a+')\n"
    "fcntl.flock(stream, fcntl.LOCK_EX)\n"
    "print('held', flush=True)\n"
    "time.sleep(120)\n"
)


def test_a_stopped_serial_run_ends_its_command_and_exits_as_the_signal_says(
    world: World, child: list[subprocess.Popen[str]]
) -> None:
    pid_file = world.folder / "stubborn.pid"
    line = f"trap '' TERM; echo $$ > {pid_file}; while :; do sleep 1; done"
    proc = serial(world, "sh", "-c", line, wait=False)
    child.append(proc)
    reached(lambda: pid_file.is_file() and pid_file.read_text().strip(), "its command")
    proc.send_signal(signal.SIGTERM)
    proc.communicate(timeout=REACH)
    assert proc.returncode == 128 + signal.SIGTERM
    with pytest.raises(ProcessLookupError):
        os.kill(int(pid_file.read_text()), 0)
    assert serial(world, "true").returncode == 0


# The polish pass of the standard track, on the same task made a task of that track.

PLAN = "docs/plans/receive.md"


def standard(world: World) -> None:
    """The task takes the standard track, with its plan in the branch."""
    committed(
        world, PLAN, "# receive\n\n## Tasks\n\n1. Say receive.\n", "docs: the plan"
    )

    def full(found: Record) -> Record:
        shape = found.task.shape and replace(found.task.shape, track="full")
        task = replace(found.task, shape=shape, plan=Plan(path=PLAN))
        return replace(found, task=task)

    state = world.checkout / ".lem" / "state"
    tasks.update(state, SLUG, full, tasks.read(state, SLUG).revision)


def polish(capsys: pytest.CaptureFixture[str], world: World, *words: str) -> Envelope:
    return lem(capsys, world.checkout, "land", "polish", SLUG, *words)


def test_the_polish_pass_keeps_its_start_and_its_run_which_the_checks_take(
    world: World, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    assert polish(capsys, world)["refusal"]["code"] == "not-due"
    standard(world)
    assert polish(capsys, world, "--done")["refusal"]["code"] == "not-started"
    assert due(capsys, world) == "polish"
    brief = polish(capsys, world)["result"]
    tip = run_git(world.worktree, "rev-parse", "HEAD")
    assert (brief["done"], brief["before"], brief["frozen"]) == (False, tip, [PLAN])
    assert brief["commits"][-1].endswith("docs: the plan")
    assert polish(capsys, world)["result"]["before"] == tip
    assert due(capsys, world) == "polish"
    committed(world, "NOTES.md", "a note the pass corrected\n", "docs: a note")
    (world.worktree / "stray.txt").write_text("nobody committed me\n")
    dirty = polish(capsys, world, "--done")["refusal"]
    assert dirty["code"] == "not-due"
    assert "changes nobody committed" in dirty["why"]
    (world.worktree / "stray.txt").unlink()
    done = polish(capsys, world, "--done")
    assert done["ok"] is True, done
    kept = record_of(world)["landing"]["polished"]
    assert (kept["before"], kept["commits"]) == (tip, 1)
    assert "run" in kept
    assert due(capsys, world) == "checks"
    ran: list[object] = []
    monkeypatch.setattr(checks_criteria, "red", lambda *given: ran.append(given))
    assert checks(capsys, world)["ok"] is True
    assert ran == []
    assert polish(capsys, world, "--done")["refusal"]["code"] == "not-due"


def test_a_pass_that_changed_the_plan_or_rewrote_the_branch_is_refused(
    world: World, capsys: pytest.CaptureFixture[str]
) -> None:
    standard(world)
    start = polish(capsys, world)["result"]["before"]
    committed(world, PLAN, "# receive\n\nanother plan\n", "docs: the plan, changed")
    refused = polish(capsys, world, "--done")["refusal"]
    assert refused["code"] == "frozen"
    assert PLAN in refused["why"]
    run_git(world.worktree, "reset", "--quiet", "--hard", f"{start}~1")
    assert polish(capsys, world, "--done")["refusal"]["code"] == "rewritten"


def test_checks_on_a_tip_that_lost_the_pass_give_the_pass_back(
    world: World, capsys: pytest.CaptureFixture[str]
) -> None:
    standard(world)
    polish(capsys, world)
    committed(world, "NOTES.md", "a note\n", "docs: a note")
    assert polish(capsys, world, "--done")["ok"] is True
    run_git(world.worktree, "reset", "--quiet", "--hard", "HEAD~1")
    committed(world, "OTHER.md", "another\n", "docs: another")
    refused = checks(capsys, world)["refusal"]
    assert refused["code"] == "no-polish"
    assert "polished" not in record_of(world)["landing"]
    assert due(capsys, world) == "polish"


def test_a_pass_after_which_the_criteria_do_not_hold_is_refused(
    world: World, capsys: pytest.CaptureFixture[str]
) -> None:
    committed(world, "check.sh", "grep -q receive README.md\n", "test: the word")
    standard(world)
    test = CriterionTest(command="sh check.sh", files=("check.sh",))

    def tested(found: Record) -> Record:
        criteria = found.task.criteria
        criterion = replace(criteria.criteria[0], tests=(test,), no_test=None)
        changed = replace(criteria, criteria=(criterion,))
        return replace(found, task=replace(found.task, criteria=changed))

    state = world.checkout / ".lem" / "state"
    tasks.update(state, SLUG, tested, tasks.read(state, SLUG).revision)
    polish(capsys, world)
    committed(world, "README.md", "The README says recieve.\n", "docs: undo")
    refused = polish(capsys, world, "--done")["refusal"]
    assert refused["code"] == "criteria"
    assert refused["why"].startswith("after the polish pass the tests of the criteria")
    assert "polished" in record_of(world)["landing"]
    assert "after" not in record_of(world)["landing"]["polished"]
