"""Park and resume, drop at each status, and the resume of a dropped task and of a task the
release stop held: the owner's words for a task he puts aside, ends or takes up again, through
the commands his session runs, on a real repository and `LocalForge`.

A drop goes from any status that is not ended, under the landing's step lock: it stops the
task's running checks, waits for any other step, and only a merge the forge made meanwhile
defeats it (the design's part 3 and part 11, choice 4; `landing.md` E, "Drop during a step").
"""

import fcntl
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from threading import Event
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
    small_built,
    small_landed,
    through,
)
from journeys.test_skeleton import BRANCH, SLUG, made
from journeys.test_standard_track import planned, shaped
from lem.kernel import clock
from lem.store import places, steps, tasks

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from io import TextIOWrapper
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
    found = ok(capsys, world, "waiting")["result"]
    assert (found["held"], [one["task"] for one in found["parked"]]) == ([], [SLUG])
    late = refused(capsys, world, "task", "move", SLUG, "building")
    assert late["code"]
    assert status(world) == "shaping"
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


HIS = 'start it, "now" — it\'s fine'


def test_a_queued_task_starts_when_the_one_before_lands_and_on_his_word_after_a_drop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    files = {"README.md": "The README says receive.\n"}
    small_built(capsys, world, "first-word", files, "fix: receive")
    ok(
        capsys,
        world,
        "task",
        "open",
        OTHER,
        "--ask",
        "and the notes",
        "--after",
        "first-word",
    )
    held = refused(capsys, world, "task", "may-start", OTHER)
    assert held["code"] == "queued"
    assert "it starts when first-word is landed or answered" in held["why"]
    small_landed(capsys, world, "first-word", "fix: receive")
    assert ok(capsys, world, "task", "may-start", OTHER)["result"]["slug"] == OTHER
    ok(capsys, world, "task", "open", "doomed", "--ask", "a doomed one")
    ok(
        capsys,
        world,
        "task",
        "open",
        "behind",
        "--ask",
        "behind it",
        "--after",
        "doomed",
    )
    drop(capsys, world, "doomed")
    stopped = refused(capsys, world, "task", "may-start", "behind")
    assert stopped["code"] == "after-dropped"
    assert stopped["fix"].startswith(
        'on his word, lem task start behind --words "HIS WORDS"'
    )
    (row,) = ok(capsys, world, "waiting")["result"]["after_dropped"]
    assert (row["task"], row["start"]) == ("behind", "start behind now")
    started = ok(capsys, world, "task", "start", "behind", "--words", HIS)["result"]
    assert (started["was"], started["status"]) == ("queued", "shaping")
    journal = tasks.read(world.checkout / places.STATE, "behind").journal
    lines = [getattr(entry, "line", None) for entry in journal]
    assert f'the owner\'s word: "{HIS}"' in lines
    assert ok(capsys, world, "waiting")["result"]["after_dropped"] == []
    assert (
        ok(capsys, world, "task", "may-start", "behind")["result"]["slug"] == "behind"
    )


@contextmanager
def during_drop(
    world: World, monkeypatch: pytest.MonkeyPatch, step: str, act: Callable[[], object]
) -> Iterator[None]:
    """Do `act` after the drop tries the held lock, then release the lock."""
    ready, attempted = Event(), Event()
    lock = fcntl.flock
    path = world.task_folder / steps.LOCK

    def observed(stream: TextIOWrapper, operation: int) -> None:
        if operation == fcntl.LOCK_EX and getattr(stream, "name", None) == str(path):
            with pytest.raises(BlockingIOError):
                lock(stream, operation | fcntl.LOCK_NB)
            attempted.set()
        lock(stream, operation)

    def held() -> None:
        with steps.step(world.checkout / places.STATE, SLUG, step, clock.now()):
            ready.set()
            assert attempted.wait(timeout=30), "the drop did not try the step lock"
            act()

    with monkeypatch.context() as patch, ThreadPoolExecutor(max_workers=1) as pool:
        patch.setattr(steps.fcntl, "flock", observed)
        worker = pool.submit(held)
        assert ready.wait(timeout=30), "the step did not take the lock"
        yield
        worker.result(timeout=30)


def test_a_drop_waits_for_another_step_and_drops_after_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    through(capsys, world, LANDING)

    def checked() -> None:
        assert status(world) == "landing"

    with during_drop(world, monkeypatch, "base", checked):
        moved = drop(capsys, world)["result"]
    assert (moved["was"], moved["status"]) == ("landing", "dropped")
    record = world.record()
    assert record["task"]["status"] == "dropped"
    assert record["journal"][-1]["line"] == WHY


def test_a_merge_on_the_forge_while_the_drop_waits_defeats_it_and_the_task_lands(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    through(capsys, world, OPEN)
    assert world.forge.pulls[1].state == "open"
    with during_drop(world, monkeypatch, "merge", lambda: world.forge.outside_merge(1)):
        said = refused(capsys, world, "task", "move", SLUG, "dropped", "--line", WHY)
    assert (said["code"], said["fix"]) == ("merged", f"lem land merged {SLUG}")
    assert "only such a merge defeats a drop, and the task lands" in said["why"]
    assert status(world) == "open"
    ok(capsys, world, "land", "merged", SLUG)
    record = world.record()
    assert record["task"]["status"] == "landed"
    assert (
        record["landing"]["merged"]["merged_head"] == world.forge.pulls[1].merged_head
    )


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
    folder = places.task_folder(world.checkout / places.STATE, new)
    assert (folder / "handoff.md").read_text().startswith("## Settled")
    assert (folder / "breaker-1.md").read_text() == DOCUMENT
    state = world.checkout / places.STATE
    assert tasks.read(state, new).release == tasks.read(state, SLUG).release
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


def test_a_failed_resume_setup_names_the_successor_and_its_breaker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capsys
) -> None:
    world = made(tmp_path, monkeypatch)
    through(capsys, world, BUILDING + 1)
    tripped(capsys, world)
    drop(capsys, world)
    team = world.checkout / ".lem" / "settings.toml"
    with team.open("a") as settings:
        settings.write('setup = ["echo half; exit 3"]\n')

    said = refused(capsys, world, "task", "resume", SLUG)
    new = f"{SLUG}-2"
    state = world.checkout / places.STATE
    record = tasks.read(state, new)
    folder = places.task_folder(state, new)
    assert status(world) == "dropped"
    assert record.task.resumed_from == SLUG
    assert hold(world, new) == "BreakerHold"
    assert (folder / "breaker-1.md").read_text() == DOCUMENT
    assert (folder / "handoff.md").is_file()
    assert (folder / "setup.log").read_text().endswith("half\n")
    assert said["code"] == "setup"
    assert "`echo half; exit 3` of checks.setup failed" in said["why"]
    assert f"{SLUG} goes on in {new}, which is held by its breaker 1" in said["why"]
    assert "correct the command" in said["fix"]


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
    assert status(world) == "building"
    (row,) = ok(capsys, world, "waiting")["result"]["blocked"]
    assert (row["task"], row["line"]) == (SLUG, stopped["why"])
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
