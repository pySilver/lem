"""The checks' rules that take facts and give a result (`model/landing/checks*.py`) and the parts
of their run that read files in a folder of their own (`app/landing/checks_*.py`): when a run
holds, the polish pass's run taken, the lines for the owner, a run that goes on too long, the
end a session that did not start the run reads, the step lock's refusals, the stale bytecode,
and the machine's one line of the runs that wait at the load gate."""

import fcntl
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import IO, TYPE_CHECKING

import msgspec
import pytest
from inline_snapshot import snapshot
from msgspec.structs import replace

from fakes.records import MOMENT, record
from lem.app.landing import (
    checks_criteria,
    checks_diff,
    checks_gate,
    checks_git,
    checks_kept,
    checks_last,
    checks_queue,
    checks_red_places,
    checks_since,
    checks_stop,
    checks_tree,
    checks_verdict,
    checks_waits,
    checks_wanted,
    checks_watch,
)
from lem.kernel.errors import Refusal
from lem.model.criteria import contract
from lem.model.landing import checks, checks_bytecode, checks_line, checks_said
from lem.model.landing.world import Due, Held
from lem.records.holds import Blocked
from lem.records.journal.landing import CheckEnd, CheckWait
from lem.records.landing.record import Landing
from lem.records.landing.start import PassRun, Polished
from lem.records.red import Inputs
from lem.records.task import Shape
from lem.records.work import Plan, Span
from lem.store import places, step_refusals, steps, tasks
from unit.landing.worlds import (
    APPROVED,
    CHECKED,
    CRITERION,
    OTHER,
    PREPARED,
    RULES,
    TIP,
    task,
    world,
)

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from lem.model.landing.checks_said import Ending
    from lem.records.record import Record

SLUG = "landing-in-the-background"
LEM_TASK = "fast-track-checks-documents"
TALK_TASK = "plan-talk-plugin-dir"


# The lines of the end of a run (`land.checks_say` on `main`).


def test_a_passed_run_names_the_review() -> None:
    assert (
        checks_said.ended(SLUG, "passed")
        == f"{SLUG}: the checks passed; the review runs, nothing for you"
    )


def test_a_passed_run_with_no_review_due_names_the_proposal() -> None:
    assert checks_said.ended(SLUG, "passed", review=False) == (
        f"{SLUG}: the checks passed; no review is due, so it is proposed, nothing for you"
    )


def test_a_red_run_names_each_command_and_the_repair() -> None:
    assert checks_said.ended(SLUG, "red", ("bash tests/all.sh",)) == (
        f"{SLUG}: the checks are red on bash tests/all.sh; a builder repairs it, "
        "nothing for you"
    )
    both = checks_said.ended(SLUG, "red", ("ruff check .", "pytest -q"))
    assert "on ruff check . and pytest -q;" in both


def test_a_refused_run_names_what_was_refused() -> None:
    said = checks_said.ended(
        SLUG, "refused", refused="a criterion's test does not hold"
    )
    assert said == (
        f"{SLUG}: the checks refused the change: a criterion's test does not hold; a "
        "builder repairs it, nothing for you"
    )


def test_a_stopped_run_waits_for_the_owner() -> None:
    assert (
        checks_said.ended(SLUG, "stopped")
        == f"{SLUG}: the checks were stopped; the landing waits for your word"
    )


def test_no_line_asks_a_question() -> None:
    lines = [
        checks_said.ended(SLUG, "passed"),
        checks_said.ended(SLUG, "red", ("x",)),
        checks_said.ended(SLUG, "refused"),
        checks_said.ended(SLUG, "stopped"),
    ]
    assert not any("?" in line for line in lines)
    assert all(line.startswith(f"{SLUG}: ") for line in lines)


def test_another_result_is_refused() -> None:
    end = {
        "kind": "check-end",
        "at": "2026-11-19T10:22:44Z",
        "outcome": "green",
        "say": "x",
    }
    with pytest.raises(msgspec.ValidationError):
        msgspec.convert(end, CheckEnd)


# A run that goes on too long, and the end a session that did not start the run reads.


def test_the_forms() -> None:
    durations = [checks_said.duration(seconds) for seconds in (26, 266, 840, 60)]
    assert durations == ["26 s", "4 min 26 s", "14 min", "1 min"]


def test_more_than_three_times_is_overdue() -> None:
    # the last run of lem-landing-page's checks: 4 min 26 s (2026-11-19)
    assert checks_said.overdue(840, 266) is not None
    assert checks_said.overdue(798, 266) is None
    assert checks_said.overdue(120, 266) is None


def test_with_no_last_run_nothing_is_overdue() -> None:
    assert checks_said.overdue(10_000, None) is None
    assert checks_said.overdue(None, 266) is None


def test_a_short_last_run_is_no_measure_in_the_first_minute() -> None:
    # a last run of `true` rounds to 0 s or 1 s, and a slow run read at 3 s or 5 s was called
    # overdue (2026-11-22)
    for last in (0, 1, 2):
        for seconds in (3, 5, 59):
            assert checks_said.overdue(seconds, last) is None
    for last in (0, 1):
        assert checks_said.overdue(61, last) is not None
    assert checks_said.overdue(10_000, 0) is not None


def test_the_floor_is_one_minute() -> None:
    assert checks_said.OVERDUE_FLOOR == 60
    assert checks_said.overdue(59, 10) is None
    assert checks_said.overdue(60, 10) is not None


def test_the_line_says_both_lengths_and_the_stop() -> None:
    assert checks_said.overdue(840, 266) == (
        "the checks run for 14 min, more than three times their last run of 4 min 26 s; "
        '"stop the checks" stops them'
    )


ENDED = datetime(2026, 11, 19, 10, 22, 44, tzinfo=UTC)


def ran(slug: str, outcome: Ending, seconds: int, at: datetime = ENDED) -> Record:
    """A task whose last run of the checks ended `outcome` at `at`, after `seconds`."""
    span = Span(name="checks", start=at - timedelta(seconds=seconds), end=at)
    end = CheckEnd(at=at, outcome=outcome, say=f"{slug}: ...")
    made = record(slug, spans=(span,))
    checked = replace(CHECKED, outcome=outcome)
    return replace(made, journal=(end,), landing=Landing(checked=checked))


def test_a_passed_end_is_past_and_the_landing_goes_on_from_its_first_step() -> None:
    said = checks_said.resumed(SLUG, ENDED, "passed")
    assert said == (
        f"{SLUG}: its last run of the checks ended at 2026-11-19T10:22Z, passed; the "
        "landing goes on from its first step, as after a cut-off"
    )
    assert "the review runs" not in said


def test_a_stopped_end_waits_for_the_owner() -> None:
    said = checks_said.resumed(SLUG, ENDED, "stopped")
    assert said.endswith("stopped; the landing waits for your word")


def test_the_end_as_status_prints_it() -> None:
    found = checks_last.ended_of(ran(SLUG, "red", 20))
    assert found is not None
    assert msgspec.to_builtins(found) == {
        "at": "2026-11-19T10:22:44Z",
        "tip": TIP[:9],
        "result": "red",
        "seconds": 20,
        "say": f"{SLUG}: ...",
        "resumed": checks_said.resumed(SLUG, ENDED, "red"),
    }
    assert checks_last.ended_of(record(SLUG)) is None


def test_the_newest_passed_end_of_any_task(tmp_path: Path) -> None:
    later = ENDED + timedelta(minutes=5)
    for made in (
        ran("one", "passed", 300),
        ran("two", "passed", 266, later),
        ran("three", "red", 20, later + timedelta(minutes=1)),
        ran("four", "stopped", 5, later + timedelta(minutes=2)),
    ):
        tasks.create(tmp_path, made)
    assert checks_last.last_seconds(tmp_path) == (266, ())


def damaged(state: Path, slug: str = "broken") -> None:
    """A task folder in `state` whose record is no record."""
    folder = state / "tasks" / slug
    folder.mkdir(parents=True)
    (folder / "task.json").write_text("{ this is no record")


def test_a_damaged_record_of_another_task_leaves_the_last_run_and_names_itself(
    tmp_path: Path,
) -> None:
    tasks.create(tmp_path, ran("two", "passed", 266))
    damaged(tmp_path)
    assert checks_last.last_seconds(tmp_path) == (266, ("broken",))


def test_no_passed_run_is_none(tmp_path: Path) -> None:
    assert checks_last.last_seconds(tmp_path) == (None, ())
    tasks.create(tmp_path, ran("one", "red", 20))
    tasks.create(tmp_path, ran("two", "refused", 400))
    assert checks_last.last_seconds(tmp_path) == (None, ())


# The step lock's refusals (`land.held_refusal` on `main`).

HOLDER = steps.Holder(
    step="checks", pid=4242, since=datetime(2026, 11, 19, 10, 18, 18, tzinfo=UTC)
)


def test_a_second_run_of_the_checks_is_refused_because_they_already_run() -> None:
    said = step_refusals.refusal(SLUG, "checks", HOLDER).why
    assert (
        f"the checks of {SLUG} already run (since 2026-11-19T10:18Z, in process 4242): a "
        "second run is refused"
    ) in said
    assert f"`lem land checks {SLUG} --status`" in said


def test_another_step_waits_for_the_end_of_the_checks() -> None:
    said = step_refusals.refusal(SLUG, "read", HOLDER).why
    assert f"the checks of {SLUG} run" in said
    assert "their end comes first" in said
    assert "the session that started them goes on when they end" in said


def test_a_step_that_holds_the_lock_is_named() -> None:
    held = replace(HOLDER, step="read", pid=7)
    said = step_refusals.refusal(SLUG, "checks", held).why
    assert f"`lem land read {SLUG}`" in said
    assert "in process 7" in said
    assert step_refusals.refusal(SLUG, "checks", None).code == "step-held"


# When a run holds: the commands that ran are the ones the checks have now (`same_checks`).


def test_the_commands_that_ran() -> None:
    assert isinstance(checks.holds(task(**PREPARED), world()), Held)


def test_a_command_added_or_removed() -> None:
    for commands in (("true", "make"), ()):
        rules = replace(RULES, commands=commands)
        assert step_of(checks.holds(task(**PREPARED), world(rules=rules))) == "checks"


def test_a_command_moved_to_serial() -> None:
    rules = replace(RULES, commands=(), serial=("true",))
    assert checks.inputs(rules) != checks.inputs(RULES)
    assert step_of(checks.holds(task(**PREPARED), world(rules=rules))) == "checks"


def test_no_command_holds_no_result() -> None:
    refused = checks.decide(task(**PREPARED), world(rules=replace(RULES, commands=())))
    assert refused is not None
    assert (refused.code, refused.why, refused.fix) == snapshot(
        (
            "no-checks",
            "the checks have no command to run, and checks that ran nothing show nothing: the project has no command in its checks in the main checkout's .lem/settings.toml",
            "add the commands to checks.commands there, then run `lem land checks fix-the-login` again",
        )
    )
    assert checks.decide(task(**PREPARED), world()) is None


def test_a_run_of_another_tip_or_not_passed_holds_not() -> None:
    assert step_of(checks.holds(task(**PREPARED), world(tip=OTHER))) == "checks"
    red = task(**{**PREPARED, "checked": replace(CHECKED, outcome="red")})
    assert checks.holds(red, world()).why == "the checks of this tip are red"


# The polish pass: due on the standard track, and its run of the criteria's tests taken.

FULL = Shape(type="feat", why="a feature", track="full")
DIGEST = "d" * 64
RUN = PassRun(inputs=DIGEST, outcome="passed", tip=TIP)
DONE = Polished(before=OTHER, after=TIP, commits=2, run=RUN, at=MOMENT)


def standard(polished: Polished | None = None) -> Record:
    """A task of the standard track at the checks, with its polish pass `polished`."""
    made = task(**PREPARED)
    landing = replace(made.landing or Landing(), polished=polished)
    return replace(made, task=replace(made.task, shape=FULL), landing=landing)


def step_of(found: Held | Due) -> str:
    """The step that is due, or `held`."""
    return found.step if isinstance(found, Due) else "held"


def test_the_fast_track_runs_the_tests() -> None:
    assert not checks.pass_kept(DONE, DIGEST, small=True)
    assert (
        checks.polished(task(**PREPARED), world()).why
        == "the fast track has no polish pass"
    )


def test_no_pass_or_one_not_done_runs_the_tests() -> None:
    assert not checks.pass_kept(None, DIGEST, small=False)
    assert not checks.pass_kept(replace(DONE, after=None), DIGEST, small=False)
    assert step_of(checks.polished(standard(), world())) == "polish"
    started = standard(polished=replace(DONE, after=None))
    assert "--done` checks what it did" in checks.polished(started, world()).why


def test_a_pass_with_no_commits_runs_the_tests() -> None:
    assert not checks.pass_kept(replace(DONE, commits=0), DIGEST, small=False)


def test_the_tip_the_pass_ended_on_takes_its_result_and_names_the_pass_and_its_commit() -> (
    None
):
    assert checks.pass_kept(DONE, DIGEST, small=False)
    assert checks.polished(standard(polished=DONE), world()).why.startswith(
        "the polish pass is done at"
    )


def test_after_decides_nothing_when_the_inputs_are_the_same() -> None:
    assert checks.pass_kept(replace(DONE, after=OTHER), DIGEST, small=False)


def test_no_inputs_now_or_a_run_with_none_runs_the_tests() -> None:
    assert not checks.pass_kept(replace(DONE, run=None), DIGEST, small=False)
    assert not checks.pass_kept(DONE, "", small=False)


def test_another_plan_file_runs_the_tests() -> None:
    # the five inputs are one digest (`records.red.Inputs`): another plan file is another one
    assert not checks.pass_kept(DONE, "e" * 64, small=False)


def test_a_red_pass_run_runs_the_tests() -> None:
    assert not checks.pass_kept(
        replace(DONE, run=replace(RUN, outcome="red")), DIGEST, small=False
    )


def test_a_tip_that_lost_the_pass_gives_it_back() -> None:
    refused = checks.unpolished(standard(polished=DONE), in_tip=False)
    assert refused is not None
    assert (refused.code, refused.why, refused.fix) == snapshot(
        (
            "no-polish",
            "the tip does not hold the polish pass's last commit (111111111): the branch was rewritten after the pass by something else than `lem land base`",
            "the pass runs again: `lem land polish fix-the-login`, its builder, and `--done`",
        )
    )
    assert checks.unpolished(standard(), in_tip=False) is None
    assert (
        checks.unpolished(standard(polished=replace(DONE, after=None)), in_tip=False)
        is None
    )
    assert checks.unpolished(standard(polished=DONE), in_tip=True) is None


# The stale bytecode the checks remove before their first command.

# git's list in a worktree with the rules `__pycache__/`, `.env`, `.venv/` and `build/`, a
# force-added `build/.gitkeep`, and an untracked `shop/` that holds only its cache
LISTED = (
    ".env",
    ".venv/",
    ":x/__pycache__/",
    "build/__pycache__/",
    "shop/",
    "shop/__pycache__/",
    "a/b/c/__pycache__/",
    "__pycache__/",
    "__pycache__.py",
    "x__pycache__/",
    "lib/__pycache__X/",
    "build/",
    "lib/__pycache__",
)


def test_a_cache_at_any_depth_goes() -> None:
    assert checks_bytecode.stale(LISTED, frozenset()) == (
        ":x/__pycache__/",
        "__pycache__/",
        "a/b/c/__pycache__/",
        "build/__pycache__/",
        "shop/__pycache__/",
    )


def test_a_cache_inside_an_ignored_folder_stays_with_it() -> None:
    assert checks_bytecode.stale(LISTED, frozenset({"build"})) == (
        ":x/__pycache__/",
        "__pycache__/",
        "a/b/c/__pycache__/",
        "shop/__pycache__/",
    )
    assert checks_bytecode.stale(("a/b/c/__pycache__/",), frozenset({"a/b"})) == ()
    assert checks_bytecode.stale(("a/b/c/__pycache__/",), frozenset({"a/bc", "b"})) == (
        "a/b/c/__pycache__/",
    )


def test_every_other_ignored_entry_stays() -> None:
    kept = (
        ".venv/",
        ".env",
        "build/",
        "shop/",
        "__pycache__.py",
        "x__pycache__/",
        "lib/__pycache__X/",
        "lib/__pycache__",
    )
    assert checks_bytecode.stale(kept, frozenset()) == ()


def test_the_folders_above_are_each_proper_folder_once() -> None:
    found = ("a/b/__pycache__/", "a/c/__pycache__/", "__pycache__/", ":x/__pycache__/")
    assert checks_bytecode.folders_above(found) == (":x", "a", "a/b", "a/c")
    assert (
        checks_bytecode.folders_above(
            checks_bytecode.candidates(("__pycache__/", ".env"))
        )
        == ()
    )


def test_git_paths_reach_the_removal_as_git_named_them(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / ".gitignore").write_text("__pycache__/\n")
    odd = tmp_path / "a\rb" / "__pycache__"
    odd.mkdir(parents=True)
    (odd / "c.pyc").write_bytes(b"\0")
    assert checks_tree.stale(tmp_path) == ("a\rb/__pycache__/",)


def test_a_folder_goes_and_a_link_inside_it_is_not_followed(tmp_path: Path) -> None:
    (tmp_path / "keep").mkdir()
    (tmp_path / "keep" / "mine.txt").write_text("mine\n")
    cache = tmp_path / "shop" / "__pycache__"
    cache.mkdir(parents=True)
    (cache / "c.pyc").write_bytes(b"\0")
    (cache / "out").symlink_to(tmp_path / "keep")
    checks_tree.removed(tmp_path, "shop/__pycache__/", SLUG)
    assert not cache.exists()
    assert (tmp_path / "shop").is_dir()
    assert (tmp_path / "keep" / "mine.txt").read_text() == "mine\n"


def test_a_link_or_a_file_of_that_name_stays(tmp_path: Path) -> None:
    (tmp_path / "keep").mkdir()
    (tmp_path / "keep" / "mine.txt").write_text("mine\n")
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "__pycache__").symlink_to(tmp_path / "keep")
    (tmp_path / "b").mkdir()
    (tmp_path / "b" / "__pycache__").write_text("a file\n")
    for folder in ("a/__pycache__/", "b/__pycache__/", "gone/__pycache__/"):
        checks_tree.removed(tmp_path, folder, SLUG)
    assert (tmp_path / "a" / "__pycache__").is_symlink()
    assert (tmp_path / "keep" / "mine.txt").read_text() == "mine\n"
    assert (tmp_path / "b" / "__pycache__").read_text() == "a file\n"


def test_a_folder_whose_parent_is_outside_the_worktree_stays(tmp_path: Path) -> None:
    root, outside = tmp_path / "root", tmp_path / "outside"
    root.mkdir()
    (outside / "__pycache__").mkdir(parents=True)
    (root / "linked").symlink_to(outside)
    checks_tree.removed(root, "linked/__pycache__/", SLUG)
    assert (outside / "__pycache__").is_dir()


def test_a_folder_that_cannot_go_refuses_with_the_fix(tmp_path: Path) -> None:
    cache = tmp_path / "shop" / "__pycache__"
    (cache / "deep").mkdir(parents=True)
    (cache / "deep" / "c.pyc").write_bytes(b"\0")
    (cache / "deep").chmod(0o500)
    try:
        with pytest.raises(Refusal) as refused:
            checks_tree.removed(tmp_path, "shop/__pycache__/", SLUG)
    finally:
        (cache / "deep").chmod(0o700)
    assert refused.value.code == "bytecode-folder"
    assert str(tmp_path.resolve() / "shop" / "__pycache__") in refused.value.why
    assert refused.value.fix == f"remove it, then run `lem land checks {SLUG}` again"


def test_what_the_commands_left_goes_and_what_was_there_stays(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "mine.txt").write_text("before the run\n")
    there = checks_tree.checks_git.untracked(tmp_path)
    (tmp_path / "out" / "deep").mkdir(parents=True)
    (tmp_path / "out" / "deep" / "x.pyc").write_bytes(b"\0")
    assert checks_tree.swept(tmp_path, there) == ("out/deep/x.pyc",)
    assert not (tmp_path / "out").exists()
    assert (tmp_path / "mine.txt").is_file()


# The machine's one line of the runs that wait at the load gate (`land.line_*` and
# `gate_look` on `main`), on a home of its own, with the clock and the load each case gives.


def at(clock: str) -> float:
    """The time of `clock`, `HH:MM` UTC of the stories' day, in seconds of the epoch."""
    hours, minutes = map(int, clock.split(":"))
    return datetime(2026, 11, 23, hours, minutes, tzinfo=UTC).timestamp()


def repository(parent: Path, name: str) -> Path:
    """A throwaway repository with Lem set up: its state folder under its checkout."""
    path = parent / name
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    (path / ".lem").mkdir()
    return path


def queued(repo: Path, slug: str, after: str, *, red: bool = False) -> None:
    """A task of `repo` that waits for `after`: queued after it, or blocked by a red base."""
    state = places.state_of(repo)
    if red:
        hold = Blocked(why="the base is red", fix="land it", after=after, since=MOMENT)
        tasks.create(state, record(slug, status="ready", hold=hold))
        return
    tasks.create(state, record(slug, status="queued", after=(after,)))


@dataclass
class Line:
    """The line in a home of its own; each run is an entry with a process id of its own, held
    by an open file of this process, as its own process holds it."""

    home: Path
    lem: Path
    lock: IO[str]
    pids: Iterator[int] = field(default_factory=lambda: iter(range(90001, 90100)))
    own: list[checks_queue.Own] = field(default_factory=list)

    @property
    def folder(self) -> Path:
        return self.home / checks_gate.LINE

    def join(self, slug: str, clock: str, repo: Path | None = None) -> checks_queue.Own:
        entry = checks_line.Entry(
            task=slug, repo=str(repo or self.lem), since=at(clock)
        )
        made = checks_queue.joined(self.folder, entry, next(self.pids))
        self.own.append(made)
        return made

    def look(
        self, own: checks_queue.Own, clock: str, load: float = 30.0, start: float = 40.0
    ) -> checks_wanted.Seen:
        found = checks_wanted.seen(
            self.lock, self.folder, own, (load, start), at(clock)
        )
        if found.look.go:
            checks_queue.leave(own)
        return found

    def names(self) -> list[str]:
        return sorted(path.name for path in self.folder.glob("*.json"))


@pytest.fixture
def line(tmp_path: Path) -> Iterator[Line]:
    home = tmp_path / "home"
    home.mkdir()
    with (home / checks_gate.LOCK).open("a+", encoding="utf-8") as lock:
        made = Line(home=home, lem=repository(tmp_path, "lem"), lock=lock)
        yield made
        for own in made.own:
            checks_queue.leave(own)


def entry(slug: str, clock: str, *, wanted: bool = False) -> checks_line.Entry:
    return checks_line.Entry(task=slug, repo="/r/lem", since=at(clock), wanted=wanted)


def test_the_order_puts_the_wait_that_began_first_first() -> None:
    found = checks_line.order((entry(TALK_TASK, "12:17"), entry(LEM_TASK, "12:01")))
    assert [one.task for one in found] == [LEM_TASK, TALK_TASK]


def test_the_run_that_looks_first_waits_behind_the_longer_wait(line: Line) -> None:
    first = line.join(LEM_TASK, "12:01")
    talk = line.join(TALK_TASK, "12:17")
    look = line.look(talk, "12:19").look
    assert (look.go, look.reason, look.behind, look.behind_repo, look.why) == (
        False,
        "behind",
        LEM_TASK,
        None,
        "longer",
    )
    assert line.names() == ["90001.json", "90002.json"]
    assert line.look(first, "12:19").look.go
    line.lock.seek(0)
    assert json.loads(line.lock.read())["task"] == LEM_TASK
    assert line.names() == ["90002.json"]
    assert line.look(talk, "12:19").look.reason == "after"
    assert line.look(talk, "12:20").look.go
    assert line.names() == []


def test_a_landing_of_one_repository_starts_before_a_later_one_of_another(
    line: Line, tmp_path: Path
) -> None:
    mybaze = repository(tmp_path, "mybaze")
    lem = line.join("keys-help-in-a-sticky-footer", "12:01")
    other = line.join("search-filters", "12:05", mybaze)
    look = line.look(other, "12:06").look
    assert (look.go, look.behind, look.behind_repo, look.why) == (
        False,
        "keys-help-in-a-sticky-footer",
        str(line.lem),
        "longer",
    )
    assert line.look(lem, "12:06").look.go


def test_the_order_puts_a_wanted_landing_before_a_longer_wait() -> None:
    found = checks_line.order(
        (
            entry("keys-help-in-a-sticky-footer", "12:00"),
            entry("fix-red-base", "12:10", wanted=True),
            entry("fix-flaky-test", "12:05", wanted=True),
        )
    )
    assert [one.task for one in found] == [
        "fix-flaky-test",
        "fix-red-base",
        "keys-help-in-a-sticky-footer",
    ]


def test_the_tasks_waited_for_are_read_from_queued_and_red_base_blocks(
    line: Line,
) -> None:
    queued(line.lem, "new-sessions-open-at-tail", "fix-red-base", red=True)
    state = places.state_of(line.lem)
    tasks.create(
        state,
        record("board-filters", status="queued", after=("fix-flaky-test", "fix-board")),
    )
    # blocked for another reason: no wait for a landing
    hold = Blocked(
        why="a builder ended two times with no report",
        fix="x",
        after="other-one",
        since=MOMENT,
    )
    tasks.create(state, record("two-builders-failed", status="ready", hold=hold))
    tasks.create(
        state, record("started-since", status="building", after=("an-old-one",))
    )
    assert checks_wanted.waited_for(state) == (
        frozenset({"fix-red-base", "fix-flaky-test", "fix-board"}),
        (),
    )


def test_the_repair_of_a_red_base_starts_before_the_longest_wait(line: Line) -> None:
    keys = line.join("keys-help-in-a-sticky-footer", "12:00")
    queued(line.lem, "new-sessions-open-at-tail", "fix-red-base", red=True)
    repair = line.join("fix-red-base", "12:10")
    look = line.look(keys, "12:11").look
    assert (look.go, look.behind, look.why) == (False, "fix-red-base", "wanted")
    assert line.look(repair, "12:11").look.go
    assert line.look(keys, "12:12").look.go


def test_a_task_queued_after_the_entries_were_made_counts_at_the_next_look(
    line: Line,
) -> None:
    keys = line.join("keys-help-in-a-sticky-footer", "12:00")
    repair = line.join("fix-red-base", "12:10")
    behind = line.look(repair, "12:11", load=45).look.behind
    assert behind == "keys-help-in-a-sticky-footer"
    queued(line.lem, "board-filters", "fix-red-base")
    assert line.look(keys, "12:12").look.behind == "fix-red-base"
    assert line.look(repair, "12:12").look.go


def test_a_damaged_record_of_another_task_counts_as_wanted_by_no_task(
    line: Line,
) -> None:
    keys = line.join("keys-help-in-a-sticky-footer", "12:00")
    queued(line.lem, "board-filters", "fix-red-base")
    state = places.state_of(line.lem)
    damaged(state)
    folder = str(state / "tasks" / "broken")
    assert checks_wanted.waited_for(state) == (frozenset({"fix-red-base"}), (folder,))
    found = line.look(keys, "12:11")
    assert found.look.go
    assert found.unread == (folder,)


def test_another_repository_whose_state_does_not_read_counts_as_wanted_by_no_task(
    line: Line, tmp_path: Path
) -> None:
    gone = tmp_path / "moved-away"
    keys = line.join("keys-help-in-a-sticky-footer", "12:00")
    line.join("fix-red-base", "11:50", gone)
    found = line.look(keys, "12:11")
    assert (found.look.behind, found.look.why, found.unread) == (
        "fix-red-base",
        "longer",
        (str(gone),),
    )
    wait = checks_said.Wait(
        load=30,
        start=40,
        behind="fix-red-base",
        behind_repo=str(gone),
        why="longer",
        unread=found.unread,
    )
    assert (
        "the state of moved-away does not read, so its landings count as wanted by no task"
    ) in checks_said.waiting("keys-help-in-a-sticky-footer", wait)


def test_the_runs_own_repository_whose_state_does_not_read_refuses_the_run(
    line: Line, tmp_path: Path
) -> None:
    own = line.join("fix-red-base", "12:10", tmp_path / "moved-away")
    with pytest.raises(Refusal):
        line.look(own, "12:11")


def test_the_second_wait_goes_after_a_wait_that_began_before_it(line: Line) -> None:
    keys = line.join("keys-help-in-a-sticky-footer", "11:58")
    assert line.look(keys, "12:00").look.go
    tail = line.join("new-sessions-open-at-tail", "12:10")
    again = line.join("keys-help-in-a-sticky-footer", "12:20")
    assert again.entry.since == at("12:20")
    look = line.look(again, "12:21").look
    assert (look.behind, look.why) == ("new-sessions-open-at-tail", "longer")
    assert line.look(tail, "12:21").look.go


def test_the_first_in_the_line_does_not_start_while_the_load_is_above_the_number(
    line: Line,
) -> None:
    first = line.join(LEM_TASK, "12:01")
    talk = line.join(TALK_TASK, "12:17")
    load_wait = line.look(first, "12:18", load=45).look
    assert (load_wait.go, load_wait.reason) == (False, "load")
    assert line.look(first, "12:18", load=40).look.reason == "load"
    assert line.look(talk, "12:18", load=45).look.reason == "behind"
    assert line.names() == ["90001.json", "90002.json"]


def test_alone_under_the_number_a_run_starts_at_its_first_look(line: Line) -> None:
    own = line.join(LEM_TASK, "12:01")
    assert line.look(own, "12:01").look.go
    line.lock.seek(0)
    assert json.loads(line.lock.read()) == {
        "at": at("12:01"),
        "task": LEM_TASK,
        "repo": str(line.lem),
    }


def test_the_next_start_comes_a_minute_after_the_one_before(line: Line) -> None:
    before = {
        "at": at("12:00"),
        "task": "keys-help-in-a-sticky-footer",
        "repo": str(line.lem),
    }
    line.lock.write(json.dumps(before))
    line.lock.flush()
    own = line.join(LEM_TASK, "12:00")
    look = line.look(own, "12:00").look
    assert (look.go, look.reason, look.after, look.gap) == (
        False,
        "after",
        "keys-help-in-a-sticky-footer",
        0,
    )
    assert line.look(own, "12:01").look.go


HOLD = (
    "import fcntl, json, sys\n"
    "handle = open(sys.argv[1], 'a+')\n"
    "fcntl.flock(handle, fcntl.LOCK_EX)\n"
    "handle.write(json.dumps({'task': 'fix-red-base', 'repo': sys.argv[2], "
    "'since': float(sys.argv[3])}))\n"
    "handle.flush()\n"
    "print('held', flush=True)\n"
    "sys.stdin.read()\n"
)


@pytest.fixture
def holder(line: Line) -> Iterator[subprocess.Popen[str]]:
    """Another run's process that holds its entry of the line until its input closes."""
    line.folder.mkdir(exist_ok=True)
    argv = [
        sys.executable,
        "-c",
        HOLD,
        str(line.folder / "4242.json"),
        str(line.lem),
        str(at("11:50")),
    ]
    child = subprocess.Popen(
        argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True
    )
    try:
        assert child.stdout is not None
        assert child.stdout.readline().strip() == "held"
        yield child
    finally:
        if child.stdin is not None and not child.stdin.closed:
            child.stdin.close()
        child.wait(timeout=30)
        if child.stdout is not None:
            child.stdout.close()


def test_an_entry_whose_process_ended_is_removed_and_the_next_run_starts(
    line: Line, holder: subprocess.Popen[str]
) -> None:
    assert holder.stdin is not None
    holder.stdin.close()
    holder.wait(timeout=30)
    own = line.join(LEM_TASK, "12:01")
    assert line.look(own, "12:02").look.go
    assert line.names() == []


def test_an_entry_whose_process_still_runs_keeps_its_place(
    line: Line, holder: subprocess.Popen[str]
) -> None:
    own = line.join(LEM_TASK, "12:01")
    look = line.look(own, "12:30").look
    assert (look.go, look.behind, look.why) == (False, "fix-red-base", "longer")
    assert line.names() == ["4242.json", "90001.json"]


def test_a_half_written_entry_with_no_holder_is_removed(line: Line) -> None:
    line.folder.mkdir()
    (line.folder / "4242.json").write_text('{"pid": 4242, "task": "fix-red-ba')
    own = line.join(LEM_TASK, "12:01")
    assert line.look(own, "12:02").look.go
    assert line.names() == []


# The wait as a whole (`land.wait_for_load` on `main`), with the gauges of the machine stood in.


@dataclass
class Gauged:
    """The load and the clock a wait reads, and what each pause does."""

    loads: list[float]
    clock: float
    paused: list[float] = field(default_factory=list)
    then: object = None

    def gauges(self) -> checks_gate.Gauges:
        return checks_gate.Gauges(
            load=self.load, clock=lambda: self.clock, sleep=self.sleep
        )

    def load(self) -> float:
        return self.loads.pop(0)

    def sleep(self, seconds: float) -> None:
        self.paused.append(seconds)
        if callable(self.then):
            self.then()


@pytest.fixture
def workspace(line: Line, monkeypatch: pytest.MonkeyPatch) -> places.Workspace:
    """The line's repository as a workspace, its task in it, and the gate's home the line's."""
    monkeypatch.setattr(
        checks_gate.folders, "home_for_writing", lambda environ: line.home
    )
    state = places.state_of(line.lem)
    tasks.create(state, record(TALK_TASK, status="landing"))
    return places.Workspace(checkout=line.lem, lem=line.lem / ".lem", state=state)


def test_a_run_behind_another_logs_the_first_and_why_then_starts_when_it_left(
    line: Line, workspace: places.Workspace
) -> None:
    first = line.join(LEM_TASK, "12:01")
    gauged = Gauged(
        loads=[30.0, 30.0], clock=at("12:19"), then=lambda: checks_queue.leave(first)
    )
    gate = checks_gate.Gate(slug=TALK_TASK, workspace=workspace, gauges=gauged.gauges())
    assert gate.passed() is True
    journal = tasks.read(workspace.state, TALK_TASK).journal
    waits = [one for one in journal if isinstance(one, CheckWait)]
    assert len(waits) == 1
    assert (waits[0].reason, waits[0].behind, waits[0].position) == (
        "behind",
        LEM_TASK,
        2,
    )
    told = checks_waits.shown(waits[0])
    assert told is not None
    assert told.wait.why == "longer"
    assert told.wait.behind_repo is None
    assert told.say == (
        f"{TALK_TASK}: the checks wait behind {LEM_TASK}, which waits longer; they start "
        "below 40"
    )
    assert line.names() == []


def test_a_stop_in_the_wait_takes_the_run_out_of_the_line(
    line: Line, workspace: places.Workspace
) -> None:
    def stop() -> None:
        raise InterruptedError(15)

    gauged = Gauged(loads=[45.0], clock=at("12:19"), then=stop)
    gate = checks_gate.Gate(slug=TALK_TASK, workspace=workspace, gauges=gauged.gauges())
    with pytest.raises(InterruptedError):
        gate.passed()
    assert line.names() == []


def test_a_gate_taken_away_starts_at_once(
    line: Line, workspace: places.Workspace
) -> None:
    (line.home / "machine.toml").write_text("[load]\nstart = 0\n")
    gauged = Gauged(loads=[], clock=at("12:19"))
    gate = checks_gate.Gate(slug=TALK_TASK, workspace=workspace, gauges=gauged.gauges())
    assert gate.passed() is False
    assert line.names() == []


def test_this_machines_number_is_read_and_a_wrong_one_refused(tmp_path: Path) -> None:
    (tmp_path / "machine.toml").write_text("[load]\nstart = 12.5\n")
    assert checks_gate.start_of(tmp_path) == 12.5
    (tmp_path / "machine.toml").write_text("[load]\nstart = -1\n")
    with pytest.raises(Refusal) as refused:
        checks_gate.start_of(tmp_path)
    assert "load.start" in refused.value.why


def test_a_new_machine_gates_at_forty(tmp_path: Path) -> None:
    assert checks_gate.start_of(tmp_path) == 40.0


def test_the_line_for_each_why() -> None:
    said = {
        why: checks_said.waiting(
            TALK_TASK, checks_said.Wait(load=30, start=40, behind=LEM_TASK, why=why)
        )
        for why in ("longer", "wanted", "first")
    }
    assert said["longer"] == (
        f"{TALK_TASK}: the checks wait behind {LEM_TASK}, which waits longer; they start "
        "below 40"
    )
    assert said["wanted"] == (
        f"{TALK_TASK}: the checks wait behind {LEM_TASK}, which another task waits for; "
        "they start below 40"
    )
    assert said["first"] == (
        f"{TALK_TASK}: the checks wait behind {LEM_TASK}, which is first in the line; they "
        "start below 40"
    )
    other = checks_said.Wait(
        load=30,
        start=40,
        behind="search-filters",
        behind_repo="/Users/me/mybaze",
        why="longer",
    )
    assert checks_said.waiting(TALK_TASK, other) == (
        f"{TALK_TASK}: the checks wait behind search-filters of mybaze, which waits longer; "
        "they start below 40"
    )
    assert checks_said.waiting(LEM_TASK, checks_said.Wait(load=45, start=40)) == (
        f"{LEM_TASK}: the checks wait for the load: 45, they start below 40"
    )


def test_two_waits_of_one_moment_say_which_is_first_in_the_line() -> None:
    first, second = checks_line.order(
        (entry(TALK_TASK, "12:17"), entry(LEM_TASK, "12:17"))
    )
    assert (first.task, checks_line.why(first, second)) == (LEM_TASK, "first")


def test_the_waits_of_status_name_the_first_and_why(tmp_path: Path) -> None:
    repo = repository(tmp_path, "lem")
    state = places.state_of(repo)
    tasks.create(state, record(TALK_TASK, status="landing"))
    folder = places.task_folder(state, TALK_TASK)
    since = datetime(2026, 11, 23, 12, 17, tzinfo=UTC)
    holder = steps.Holder(step="checks", pid=os.getpid(), since=since, run="new")
    for why in ("longer", "wanted", "first"):
        wait = checks_said.Wait(
            load=30, start=40, behind=LEM_TASK, behind_repo="/Users/me/mybaze", why=why
        )
        entry = checks_waits.wait_of(wait, TALK_TASK, 2, since.timestamp(), run="new")
        checks_waits.noted(state, TALK_TASK, entry)
        found = checks_since.running(tasks.read(state, TALK_TASK), state, holder, since)
        assert found.waits is not None
        assert found.waits.wait == wait
        assert found.waits.say == checks_said.waiting(TALK_TASK, wait)
    # Another run in the same second does not show the wait of the first one.
    another = replace(holder, run="another")
    found = checks_since.running(tasks.read(state, TALK_TASK), state, another, since)
    assert found.waits is None
    wait = checks_said.Wait(load=32, start=40, after=LEM_TASK, unread=("/repos/other",))
    entry = checks_waits.wait_of(wait, TALK_TASK, 1, since.timestamp(), run="another")
    checks_waits.noted(state, TALK_TASK, entry)
    saved = tasks.read(state, TALK_TASK)
    earlier = Span(name="checks", start=since)
    saved = replace(saved, task=replace(saved.task, spans=(earlier,)))
    found = checks_since.running(saved, state, another, since)
    assert entry.reason == "after"
    assert found.waits is not None and found.waits.wait == wait
    assert found.waits.say == checks_said.waiting(TALK_TASK, wait)
    assert not (folder / "checks-wait.json").exists()


def test_a_lock_file_of_no_holder_is_free_and_a_held_one_is_not(tmp_path: Path) -> None:
    path = tmp_path / "4242.json"
    path.write_text('{"task": "x", "repo": "/r", "since": 1.0}')
    assert checks_queue.held(path) is None
    assert not path.exists()
    with path.open("a+") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.write('{"task": "x", "repo": "/r", "since": 1.0}')
        stream.flush()
        assert checks_queue.held(path) == checks_line.Entry(
            task="x", repo="/r", since=1.0
        )


def test_a_second_entry_of_one_process_is_refused(line: Line) -> None:
    entry_of_run = checks_line.Entry(
        task=LEM_TASK, repo=str(line.lem), since=at("12:01")
    )
    line.own.append(checks_queue.joined(line.folder, entry_of_run, 4242))
    with pytest.raises(Refusal) as refused:
        checks_queue.joined(line.folder, entry_of_run, 4242)
    assert refused.value.code == "line"
    assert "4242.json for a run that still waits" in refused.value.why


def test_a_git_that_fails_is_refused_in_its_words(tmp_path: Path) -> None:
    with pytest.raises(Refusal) as refused:
        checks_tree.stale(tmp_path)
    assert refused.value.code == "git"
    assert refused.value.why.startswith("git ls-files --others failed: ")


@pytest.mark.skipif(os.geteuid() == 0, reason="a root user may stop any process")
def test_checks_another_user_runs_are_not_stopped() -> None:
    with pytest.raises(Refusal) as refused:
        checks_watch.termed(SLUG, 1)
    assert refused.value.code == "stop"
    assert refused.value.fix == "the user that started them stops them"


def test_a_run_that_does_not_end_after_its_stop_is_refused_with_the_way_on(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / steps.LOCK
    holder = steps.Holder(step="checks", pid=os.getpid(), since=MOMENT)
    path.write_text(msgspec.json.encode(holder).decode())
    monkeypatch.setattr(checks_watch, "STOP_WAIT", 0.3)
    with pytest.raises(Refusal) as refused:
        checks_watch.waited(SLUG, path, os.getpid())
    assert refused.value.code == "stop"
    assert f"`lem land checks {SLUG} --stop` asks again" in refused.value.fix


# The review of 2026-11-25 (`/tmp/lem-rebuild/reviews/land-checks/findings.md`): each case
# failed on the code before its change.


def test_a_git_that_cannot_give_the_diff_is_refused_never_read_as_no_change(
    tmp_path: Path,
) -> None:
    for read in (checks_diff.diff, checks_diff.rows):
        with pytest.raises(Refusal) as refused:
            read(tmp_path, "a" * 40, "b" * 40)
        assert refused.value.code == "git"
    with pytest.raises(Refusal):
        checks_git.changed(tmp_path)


def test_a_check_ignore_that_fails_is_refused_in_its_words(tmp_path: Path) -> None:
    with pytest.raises(Refusal) as refused:
        checks_tree.ignored_of(tmp_path, ("build",))
    assert refused.value.code == "git"
    assert refused.value.why.startswith("git check-ignore --no-index failed: ")


def test_a_second_term_while_the_first_is_handled_changes_nothing() -> None:
    stopper = checks_stop.Stopper()
    with pytest.raises(InterruptedError):
        stopper(15, None)
    stopper(15, None)
    stopper.done = True
    stopper(15, None)


def test_the_last_passed_run_is_found_behind_a_red_retry(tmp_path: Path) -> None:
    passed = ran("one", "passed", 266)
    later = ENDED + timedelta(minutes=10)
    retry = CheckEnd(at=later, outcome="red", say="one: ...")
    spans = (
        *passed.task.spans,
        Span(name="checks", start=later - timedelta(seconds=20), end=later),
    )
    tasks.create(
        tmp_path,
        replace(
            passed,
            task=replace(passed.task, spans=spans),
            journal=(*passed.journal, retry),
        ),
    )
    assert checks_last.last_seconds(tmp_path) == (266, ())


def test_a_new_place_in_the_line_is_told_again(
    line: Line, workspace: places.Workspace
) -> None:
    gate = checks_gate.Gate(
        slug=TALK_TASK,
        workspace=workspace,
        gauges=Gauged(loads=[], clock=at("12:19")).gauges(),
    )
    wait = checks_said.Wait(load=30, start=40, behind=LEM_TASK, why="longer")
    gate.tell(wait, 3)
    gate.tell(wait, 2)
    journal = tasks.read(workspace.state, TALK_TASK).journal
    assert [one.position for one in journal if isinstance(one, CheckWait)] == [3, 2]


def test_a_stop_during_the_criteria_tests_stays_a_stop_once_the_worktrees_are_gone(
    tmp_path: Path,
) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    found = (tmp_path / "x.red-tip", tmp_path / "x.red-base")
    with pytest.raises(InterruptedError), checks_red_places.kept(tmp_path, found, "x"):
        raise InterruptedError(15)


@pytest.mark.parametrize("field", ["tip", "base", "plan", "setup", "serial"])
def test_each_of_the_five_inputs_that_differs_runs_the_tests(field: str) -> None:
    found = Inputs(
        tip="1" * 40, base="2" * 40, plan="docs/plans/p.md", setup=("make",), serial=()
    )
    other = {
        "tip": "3" * 40,
        "base": "4" * 40,
        "plan": "docs/plans/q.md",
        "setup": (),
        "serial": ("e2e",),
    }
    kept = replace(DONE, run=replace(RUN, inputs=checks_criteria.digest(found)))
    now = checks_criteria.digest(replace(found, **{field: other[field]}))
    assert checks.pass_kept(kept, checks_criteria.digest(found), small=False)
    assert not checks.pass_kept(kept, now, small=False)


def test_the_length_of_a_run_is_the_monotonic_clocks_when_the_wall_clock_went_back() -> (
    None
):
    before = task(**PREPARED)
    verdict = checks_verdict.Verdict(
        run=replace(CHECKED, at=MOMENT),
        contract=contract.mark(before.task),
        seconds=42,
    )
    earlier = MOMENT - timedelta(hours=1)
    end = checks_kept.end_of(before, world(), verdict, earlier)
    assert end.seconds == 42


def test_a_pass_of_a_contract_that_moved_since_it_began_is_not_written() -> None:
    before = task(**PREPARED)
    verdict = checks_verdict.Verdict(run=CHECKED, contract=contract.mark(before.task))
    other = replace(
        APPROVED, criteria=(replace(CRITERION, text="The login works twice."),)
    )
    moved = replace(
        before,
        task=replace(
            before.task,
            criteria=replace(before.task.criteria, approvals=(APPROVED, other)),
        ),
    )
    assert checks_kept.kept(before, world=world(), verdict=verdict, at=MOMENT).landing
    with pytest.raises(Refusal) as refused:
        checks_kept.kept(moved, world=world(), verdict=verdict, at=MOMENT)
    assert refused.value.code == "contract-moved"


@pytest.mark.parametrize(
    "fields",
    [
        {"digest": "new-digest"},
        {"criteria": (replace(CRITERION, text="The login works twice."),)},
        {"approvals": ()},
    ],
)
def test_edits_to_the_criteria_or_their_approval_require_a_new_run(
    fields: dict[str, object],
) -> None:
    before = task().task.criteria
    assert checks.moved(before, replace(before, how="Explain the flow.")) is None
    refused = checks.moved(before, replace(before, **fields))
    assert refused is not None
    assert (refused.code, refused.why, refused.fix) == (
        "contract-moved",
        "the criteria changed while the checks ran, so their run is not one of the criteria of now",
        "the checks run again on the criteria of now: lem land next names the step",
    )


def test_with_no_origin_the_base_branch_itself(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    assert checks_red_places.onto_of(tmp_path, "main") == "main"
    subprocess.run(
        ["git", "-C", str(tmp_path), "remote", "add", "origin", "/x"], check=True
    )
    assert checks_red_places.onto_of(tmp_path, "main") == "origin/main"


def test_changes_to_the_plan_path_and_criteria_invalidate_checks() -> None:
    path = "docs/plans/fix-login.md"
    checked = replace(
        CHECKED, inputs=checks.inputs(RULES, path), criteria_digest="before"
    )
    record = task(checked=checked)
    criteria = replace(record.task.criteria, digest="before")
    shaped = replace(record.task, criteria=criteria, plan=Plan(path=path))
    done = replace(record, task=shaped)
    assert checks.holds(done, world()) == Held(why="the checks passed on this tip")
    moved = replace(done, task=replace(shaped, plan=Plan(path="docs/plans/other.md")))
    assert checks.holds(moved, world()) == Due(
        step="checks",
        why="the check definitions changed since the run: commands, serial, setup or the plan path",
    )
    changed = replace(
        done, task=replace(shaped, criteria=replace(criteria, digest="after"))
    )
    assert checks.holds(changed, world()) == Due(
        step="checks", why="the tests of the criteria changed since the checks ran"
    )


def test_a_proved_backlog_filing_keeps_checks_on_the_previous_tip() -> None:
    record = task(**PREPARED)
    assert checks.holds(record, world(tip=OTHER, item_chain=(TIP, OTHER))) == Held(
        why="the checks passed on this tip"
    )
    assert checks.holds(record, world(tip=OTHER)) == Due(
        step="checks", why="no run of the checks covers this tip on its base"
    )


def test_a_standard_track_names_the_polish_step_and_the_commits() -> None:
    assert checks.polished(standard(), world()) == Due(
        step="polish",
        why=(
            "fix-the-login takes the standard track, and no polish pass is on record for "
            "this landing: `lem land polish fix-the-login` starts it"
        ),
    )
    started = standard(polished=replace(DONE, after=None))
    assert checks.polished(started, world()) == Due(
        step="polish",
        why=(
            "the polish pass started at 999999999 and is not done: after its builder, "
            "`lem land polish fix-the-login --done` checks what it did"
        ),
    )
    assert checks.polished(standard(polished=DONE), world()) == Held(
        why="the polish pass is done at 111111111"
    )


def test_a_recorded_check_end_without_details_still_gives_a_next_step() -> None:
    assert checks_said.ended(SLUG, "red") == (
        f"{SLUG}: the checks are red on a command; a builder repairs it, nothing for you"
    )
    assert checks_said.ended(SLUG, "refused") == (
        f"{SLUG}: the checks refused the change: the step met an error; a builder repairs it, "
        "nothing for you"
    )


def test_a_wait_names_each_repository_it_could_not_read() -> None:
    wait = checks_said.Wait(
        load=36, start=40, behind="fix-login", unread=("/work/shop", "/work/studio")
    )
    assert checks_said.waiting(SLUG, wait) == (
        f"{SLUG}: the checks wait behind fix-login, which is first in the line; they start below 40"
        "; the state of shop does not read, so its landings count as wanted by no task"
        "; the state of studio does not read, so its landings count as wanted by no task"
    )


def test_more_than_one_proved_filing_commit_keeps_the_run() -> None:
    current = "4" * 40
    chain = (TIP, OTHER, current)
    assert checks.holds(task(**PREPARED), world(tip=current, item_chain=chain)) == Held(
        why="the checks passed on this tip"
    )
