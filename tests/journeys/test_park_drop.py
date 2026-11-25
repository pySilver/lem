"""Park and resume, drop at each status, and the resume of a dropped task and of a task the
release stop held: the owner's words for a task he puts aside, ends or takes up again, through
the commands his session runs, on a real repository and `LocalForge`.

A drop goes from any status that is not ended, under the landing's step lock: it stops the
task's running checks, waits for any other step, and only a merge the forge made meanwhile
defeats it (the design's part 3 and part 11, choice 4; `landing.md` E, "Drop during a step").
"""

import signal
import subprocess
import sys
from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from fakes.repo import run_git
from journeys.agent import (
    BUILDING,
    LANDING,
    OPEN,
    READY,
    SHAPING,
    ok,
    refused,
    through,
)
from journeys.test_skeleton import BRANCH, SLUG, made
from journeys.test_standard_track import planned, shaped
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from journeys.test_skeleton import Envelope, World
    from lem.records.record import Record

type Capsys = pytest.CaptureFixture[str]

WHY = "the owner has a better idea"
OTHER = "notes-say-receive"


def status(world: World, slug: str = SLUG) -> str:
    return tasks.read(world.checkout / places.STATE, slug).task.status


def hold(world: World, slug: str = SLUG) -> str | None:
    found = tasks.read(world.checkout / places.STATE, slug).task.hold
    return None if found is None else type(found).__name__


def drop(capsys: Capsys, world: World, slug: str = SLUG) -> Envelope:
    return ok(capsys, world, "task", "move", slug, "dropped", "--line", WHY)


def listed(capsys: Capsys, world: World, *words: str) -> list[str]:
    rows = ok(capsys, world, "task", "list", *words)["result"]
    return [row["slug"] for row in rows]


# ---- park and resume ----


def test_a_task_that_waits_for_the_owner_is_parked_and_comes_back_as_it_was(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    ok(capsys, world, "task", "open", SLUG, "--ask", "the README says recieve")
    read = (
        "--type",
        "docs",
        "--why",
        "a word",
        "--track",
        "small",
        "--wait",
        "request",
    )
    ok(capsys, world, "task", "read", SLUG, *read)
    assert hold(world) == "OwnerHold"
    waits = ok(capsys, world, "waiting")["result"]
    assert SLUG in str(waits)
    parked = ok(capsys, world, "task", "park", SLUG, "--why", "after the release")
    assert parked["result"]["resumed"] == "parked"
    assert hold(world) == "Parked"
    assert status(world) == "shaping"
    assert refused(capsys, world, "task", "may-start", SLUG)["code"]
    back = ok(capsys, world, "task", "resume", SLUG)["result"]
    assert (back["resumed"], back["status"]) == ("parked", "shaping")
    assert hold(world) == "OwnerHold"


def test_a_task_an_agent_works_on_is_not_parked_and_a_planned_one_is(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    through(capsys, world, BUILDING)
    said = refused(capsys, world, "task", "park", SLUG, "--why", "later")
    assert said["code"] == "park"
    assert said["fix"] == f"lem task move {SLUG} dropped --line WHY drops it"
    assert hold(world) is None
    other = made(tmp_path / "standard", monkeypatch)
    shaped(capsys, other)
    planned(capsys, other)
    ok(capsys, other, "task", "park", SLUG, "--why", "after the release")
    assert (status(other), hold(other)) == ("planned", "Parked")
    assert refused(capsys, other, "task", "build", SLUG)["code"]
    ok(capsys, other, "task", "resume", SLUG)
    assert (status(other), hold(other)) == ("planned", None)
    assert ok(capsys, other, "task", "build", SLUG)["result"]["status"] == "building"


# ---- drop at each status ----

STATUSES = (
    ("shaping", SHAPING),
    ("building", BUILDING),
    ("ready", READY),
    ("landing", LANDING),
    ("open", OPEN),
)


@pytest.mark.parametrize(("was", "count"), STATUSES, ids=[one for one, _ in STATUSES])
def test_a_drop_ends_a_task_at_each_status_and_leaves_its_pull_request_to_him(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: Capsys,
    was: str,
    count: int,
) -> None:
    world = made(tmp_path, monkeypatch)
    through(capsys, world, count)
    assert status(world) == was
    moved = drop(capsys, world)["result"]
    assert (moved["was"], moved["status"]) == (was, "dropped")
    assert listed(capsys, world) == []
    assert listed(capsys, world, "--ended") == [SLUG]
    again = refused(capsys, world, "task", "move", SLUG, "building")
    assert again["code"]
    assert status(world) == "dropped"
    if was == "open":
        assert world.forge.pulls[1].state == "open"
        assert world.forge.merge_calls == []


def test_a_queued_and_a_planned_task_are_dropped_too(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    ok(capsys, world, "task", "open", SLUG, "--ask", "the README says recieve")
    ok(capsys, world, "task", "open", OTHER, "--ask", "and the notes", "--after", SLUG)
    assert status(world, OTHER) == "queued"
    assert drop(capsys, world, OTHER)["result"]["was"] == "queued"
    standard = made(tmp_path / "standard", monkeypatch)
    shaped(capsys, standard)
    planned(capsys, standard)
    assert drop(capsys, standard)["result"]["was"] == "planned"


# A process that holds a task's step lock, for the step named, until it is killed.
HOLDER = """
import sys, time
from datetime import UTC, datetime
from pathlib import Path
from lem.store import steps
with steps.step(Path(sys.argv[1]), sys.argv[2], sys.argv[3], datetime.now(UTC).replace(microsecond=0)):
    print("held", flush=True)
    time.sleep(float(sys.argv[4]))
    Path(sys.argv[5]).touch()
"""


def holder(world: World, step: str, seconds: float) -> subprocess.Popen[str]:
    """A process that holds the task's step lock for `step` for `seconds`, and touches the
    file `released` of the journey's folder as it lets the lock go."""
    state = world.checkout / places.STATE
    words = (str(state), SLUG, step, str(seconds), str(world.folder / "released"))
    child = subprocess.Popen(
        [sys.executable, "-I", "-B", "-c", HOLDER, *words],
        stdout=subprocess.PIPE,
        text=True,
    )
    assert child.stdout is not None
    assert child.stdout.readline().strip() == "held"
    return child


def test_a_drop_during_the_checks_stops_them_and_takes_the_step_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    through(capsys, world, LANDING + 1)
    checks = holder(world, "checks", 120)
    try:
        assert drop(capsys, world)["result"]["status"] == "dropped"
        assert checks.wait(timeout=30) == -signal.SIGTERM
    finally:
        checks.kill()
        checks.wait()
    assert refused(capsys, world, "land", "checks", SLUG)["code"]


def test_a_drop_waits_for_another_step_and_drops_after_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    through(capsys, world, LANDING)
    base = holder(world, "base", 3)
    try:
        assert drop(capsys, world)["result"]["status"] == "dropped"
        assert (world.folder / "released").is_file()
        assert base.wait(timeout=30) == 0
    finally:
        base.kill()
        base.wait()


def test_a_merge_on_the_forge_while_the_drop_waits_defeats_it_and_the_task_lands(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    through(capsys, world, OPEN)
    world.forge.outside_merge(1)
    said = refused(capsys, world, "task", "move", SLUG, "dropped", "--line", WHY)
    assert (said["code"], said["fix"]) == ("merged", f"lem land merged {SLUG}")
    assert status(world) == "open"
    ok(capsys, world, "land", "merged", SLUG)
    assert status(world) == "landed"


# ---- the resume of a dropped task ----

DOCUMENT = """# The README's word is in a file the build may not change

## Today and after

**Today**:

1. The README says recieve.
2. The build stops.

**After**:

1. The README says receive.
2. The task lands.

## The case that broke

1. The README is generated from docs/readme.in.
2. The build changed README.md alone.

```mermaid
flowchart TD
  A["README.md"] --> B["generated again"]
```

## The root cause

The plan did not know the README is generated.

## The options

| | A: the source | B: the file |
| --- | --- | --- |
| Sees | receive for good | recieve again |

## The recommendation

A: the source.

## The assumptions

- Nothing else generates the README.
"""


def tripped(capsys: Capsys, world: World) -> None:
    """The lead's breaker over the building task: its document and its handoff."""
    folder = world.task_folder
    (folder / "breaker.md").write_text(DOCUMENT)
    (folder / "handoff.md").write_text("## Settled\n\n- the word is receive\n")
    ok(capsys, world, "decisions", "breaker", SLUG, "--cause", "criteria")


def test_a_dropped_task_with_a_breaker_goes_on_in_a_new_task_from_its_commits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    through(capsys, world, BUILDING + 1)
    tripped(capsys, world)
    assert hold(world) == "BreakerHold"
    ok(capsys, world, "task", "park", SLUG, "--why", "after lunch")
    back = ok(capsys, world, "task", "resume", SLUG)["result"]
    assert (back["resumed"], back["breaker"]) == ("parked", 1)
    assert hold(world) == "BreakerHold"
    drop(capsys, world)
    tip = run_git(world.checkout, "rev-parse", BRANCH)
    resumed = ok(capsys, world, "task", "resume", SLUG)["result"]
    new = resumed["task"]
    assert (resumed["resumed"], resumed["from"], resumed["breaker"]) == (
        "dropped",
        SLUG,
        1,
    )
    assert new == f"{SLUG}-2"
    assert status(world) == "dropped"
    assert hold(world, new) == "BreakerHold"
    worktree = world.checkout / ".lem" / "worktrees" / new
    assert run_git(worktree, "rev-parse", "HEAD") == tip
    copied = places.task_folder(world.checkout / places.STATE, new) / "handoff.md"
    assert copied.read_text().startswith("## Settled")
    again = refused(capsys, world, "task", "resume", SLUG)
    assert again["code"] == "resumed"


def test_a_dropped_task_with_no_breaker_is_no_resume(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    through(capsys, world, SHAPING)
    drop(capsys, world)
    said = refused(capsys, world, "task", "resume", SLUG)
    assert said["code"] == "resume"
    assert said["fix"].startswith("new work for it is a new ask: /lem ")


def two_back(world: World) -> None:
    """The task's record says it began on a release two before the running one."""

    def old(found: Record) -> Record:
        return replace(found, release="0.0.1")

    state = world.checkout / places.STATE
    tasks.update(state, SLUG, old, tasks.read(state, SLUG).revision)


def test_a_task_the_release_stop_held_is_dropped_and_goes_on_as_a_new_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    through(capsys, world, BUILDING + 1)
    two_back(world)
    stopped = refused(capsys, world, "task", "move", SLUG, "ready")
    assert stopped["code"] == "release"
    assert hold(world) == "ReleaseHold"
    assert refused(capsys, world, "task", "resume", SLUG)["code"] == "release"
    drop(capsys, world)
    assert hold(world) == "ReleaseHold"
    resumed = ok(capsys, world, "task", "resume", SLUG)
    found = resumed["result"]
    assert (found["resumed"], found["from"], found.get("breaker")) == (
        "request",
        SLUG,
        None,
    )
    assert resumed["next"]["command"] == f"lem session open {found['task']} --why new"
    new = tasks.read(world.checkout / places.STATE, found["task"])
    assert new.release != "0.0.1"
    worktree = world.checkout / ".lem" / "worktrees" / found["task"]
    assert run_git(worktree, "log", "-1", "--format=%s") == "docs: receive"
