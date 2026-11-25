"""The wakes the board server owes a task's session: the end of its landing, a conflict, a
refused merge, and the turn of a queued task, each once, on the fake terminal."""

from datetime import timedelta
from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from fakes.records import MOMENT
from lem.app.landing.merged import CLOSED
from lem.app.sessions import acts, log, opening
from lem.board.duties import conflict, queue
from lem.board.duties.memory import Kept
from lem.records.holds import ReleaseHold
from lem.records.journal.task import StateNoted
from lem.store import tasks
from lem.store.retention.run import pruned
from unit.board.duties.world import duty_of, landing_of, looked, opened
from unit.owner.looked import proposed, refused
from unit.sessions.terminal import with_caller
from unit.sessions.world import SLUG, here_of, made

if TYPE_CHECKING:
    from pathlib import Path

    from lem.app.sessions.here import Here

LATER = MOMENT + timedelta(minutes=5)
HOUR = MOMENT + timedelta(hours=1)
OTHER = "d" * 40


def wakes(here: Here, slug: str = SLUG) -> list[tuple[str, str | None]]:
    """Each wake and each open of the task on record, with its why and head."""
    found = log.read(here.folder(slug))
    heads: list[tuple[str, str | None]] = [
        (act.why, act.head) for act in found if isinstance(act, acts.Wake)
    ]
    opens: list[tuple[str, str | None]] = [
        (act.why, None) for act in found if isinstance(act, acts.Open)
    ]
    return opens + heads


def worktree(here: Here, slug: str = SLUG) -> None:
    """The task's worktree, as git leaves it."""
    folder = here.where.checkout / ".lem" / "worktrees" / slug
    folder.mkdir(parents=True)
    (folder / ".git").write_text("gitdir: elsewhere\n")


def test_a_merge_wakes_the_tasks_session_once_while_its_worktree_stays(
    tmp_path: Path,
) -> None:
    terminal = with_caller()
    here = here_of(tmp_path, terminal)
    made(here, status="landed", since=LATER)
    gone = made(here, "no-worktree", status="landed", since=LATER).task.slug
    worktree(here)
    kept = Kept()
    conflict.tick(duty_of(here, HOUR, kept))
    conflict.tick(duty_of(here, HOUR + timedelta(minutes=1), kept))
    assert wakes(here) == [("merged", None)]
    assert wakes(here, gone) == []


@pytest.mark.parametrize("seconds_before_end", [0, 1])
def test_an_end_wake_counts_when_the_tick_stamp_is_at_or_before_the_end(
    tmp_path: Path, seconds_before_end: int
) -> None:
    here = here_of(tmp_path)
    made(here, status="landed", since=LATER)
    worktree(here)
    tick = LATER - timedelta(seconds=seconds_before_end)

    conflict.tick(duty_of(here, tick))
    conflict.tick(duty_of(here, HOUR))

    assert wakes(here) == [("merged", None)]


def test_a_pruned_forge_close_still_wakes_the_tasks_session(tmp_path: Path) -> None:
    here = here_of(tmp_path)
    found = made(here, status="dropped", since=LATER)
    entry = StateNoted(at=LATER, status="dropped", line=f"{CLOSED}: #44 is closed")
    tasks.update(
        here.where.state,
        SLUG,
        lambda one: replace(one, journal=(entry,)),
        found.revision,
    )
    worktree(here)
    pruned(here.where.state, 30, "test", LATER + timedelta(days=31), dry=False)

    conflict.tick(duty_of(here, LATER + timedelta(days=31)))

    assert wakes(here) == [("merged", None)]


def test_a_task_the_forge_closed_is_woken_and_one_dropped_otherwise_is_not(
    tmp_path: Path,
) -> None:
    here = here_of(tmp_path)
    closed = StateNoted(at=LATER, status="dropped", line=f"{CLOSED}: #44 is closed")
    own = StateNoted(at=LATER, status="dropped", line="the owner dropped it")
    for slug, entry in (("closed-task", closed), ("own-drop", own)):
        found = made(here, slug, status="dropped", since=LATER)
        tasks.update(
            here.where.state,
            slug,
            lambda one, e=entry: replace(one, journal=(e,)),
            found.revision,
        )
        worktree(here, slug)
    conflict.tick(duty_of(here, HOUR))
    assert wakes(here, "closed-task") == [("merged", None)]
    assert wakes(here, "own-drop") == []


def test_a_conflict_wakes_the_session_once_for_each_head(tmp_path: Path) -> None:
    terminal = with_caller()
    here = here_of(tmp_path, terminal)
    opened(here, SLUG, proposed=proposed())
    opening.open_session(here, SLUG, "new", None, LATER)
    looked(here, SLUG, "CONFLICTING")
    kept = Kept()
    conflict.tick(duty_of(here, HOUR, kept))
    conflict.tick(duty_of(here, HOUR + timedelta(minutes=1), kept))
    assert wakes(here) == [("new", None), ("conflict", "a" * 40)]
    assert terminal.told == [("session-1", f"lem: {SLUG} conflict")]


def test_a_new_proposal_after_a_conflict_is_woken_again_and_another_head_never(
    tmp_path: Path,
) -> None:
    here = here_of(tmp_path)
    found = opened(here, SLUG, proposed=proposed())
    looked(here, SLUG, "CONFLICTING")
    conflict.tick(duty_of(here, LATER))
    newer = replace(proposed(), at=HOUR)
    landing = replace(landing_of(found), proposed=newer)
    tasks.update(here.where.state, SLUG, lambda one: replace(one, landing=landing), 1)
    conflict.tick(duty_of(here, HOUR + timedelta(minutes=1)))
    looked(here, SLUG, "CONFLICTING", head=OTHER)
    conflict.tick(duty_of(here, HOUR + timedelta(minutes=2)))
    woken = [act for act in log.read(here.folder(SLUG)) if isinstance(act, acts.Wake)]
    assert [(one.why, one.head) for one in woken] == [("conflict", "a" * 40)] * 2


def test_after_a_merge_an_open_task_with_no_conflict_waits_as_it_is(
    tmp_path: Path,
) -> None:
    here = here_of(tmp_path)
    opened(here, SLUG, proposed=proposed())
    looked(here, SLUG, "MERGEABLE")
    conflict.tick(duty_of(here, HOUR))
    assert wakes(here) == []


def test_a_refused_merge_wakes_the_session_once_and_githubs_own_refusal_never(
    tmp_path: Path,
) -> None:
    here = here_of(tmp_path)
    merger = replace(refused("lem", "rule"), by="merger")
    opened(here, "by-merger", proposed=proposed(), refused=merger)
    opened(here, "moved-base", proposed=proposed(), refused=refused("lem", "base"))
    opened(here, "by-github", proposed=proposed(), refused=refused("github", "rule"))
    kept = Kept()
    conflict.tick(duty_of(here, HOUR, kept))
    conflict.tick(duty_of(here, HOUR + timedelta(minutes=1), kept))
    assert [why for why, _ in wakes(here, "by-merger")] == ["refused"]
    assert [why for why, _ in wakes(here, "moved-base")] == ["refused"]
    assert wakes(here, "by-github") == []


def test_a_task_two_releases_back_is_not_woken(tmp_path: Path) -> None:
    here = here_of(tmp_path)
    found = opened(here, SLUG, proposed=proposed())
    hold = ReleaseHold(
        began="0.1.0", running="0.3.0", say="it began two releases back", since=MOMENT
    )
    task = replace(found.task, hold=hold)
    tasks.update(here.where.state, SLUG, lambda one: replace(one, task=task), 1)
    looked(here, SLUG, "CONFLICTING")
    conflict.tick(duty_of(here, HOUR))
    assert wakes(here) == []


def test_a_queued_task_gets_its_turn_once_when_its_tasks_ended(tmp_path: Path) -> None:
    terminal = with_caller()
    here = here_of(tmp_path, terminal)
    made(here, "first", status="landed", since=LATER)
    made(here, "second", status="answered", since=LATER)
    made(here, "third", status="building", since=LATER)
    made(here, status="queued", after=("first", "second"), lead="builder")
    made(here, "waits", status="queued", after=("first", "third"), lead="builder")
    kept = Kept()
    queue.tick(duty_of(here, HOUR, kept))
    queue.tick(duty_of(here, HOUR + timedelta(minutes=1), kept))
    assert wakes(here) == [("queue", None)]
    assert wakes(here, "waits") == []
    assert len(terminal.openings) == 1


def test_a_queued_task_whose_session_lives_is_woken_and_a_dropped_one_waits(
    tmp_path: Path,
) -> None:
    terminal = with_caller()
    here = here_of(tmp_path, terminal)
    made(here, "first", status="landed", since=LATER)
    made(here, "gone", status="dropped", since=LATER)
    made(here, status="building", lead="builder")
    opening.open_session(here, SLUG, "new", None, MOMENT)
    task = replace(
        tasks.read(here.where.state, SLUG).task,
        status="queued",
        after=("first",),
        since=LATER,
    )
    tasks.update(here.where.state, SLUG, lambda one: replace(one, task=task), 1)
    made(here, "behind-gone", status="queued", after=("gone",), lead="builder")
    queue.tick(duty_of(here, HOUR))
    assert terminal.told == [("session-1", f"lem: {SLUG} queue")]
    assert wakes(here, "behind-gone") == []


def test_a_task_queued_again_behind_a_second_task_gets_its_turn_when_that_one_ends(
    tmp_path: Path,
) -> None:
    here = here_of(tmp_path)
    made(here, "first", status="landed", since=LATER)
    made(here, status="queued", after=("first",), lead="builder", since=LATER)
    queue.tick(duty_of(here, LATER + timedelta(minutes=1)))
    made(here, "second", status="landed", since=HOUR)
    task = replace(
        tasks.read(here.where.state, SLUG).task, after=("second",), since=HOUR
    )
    tasks.update(here.where.state, SLUG, lambda one: replace(one, task=task), 1)
    queue.tick(duty_of(here, HOUR + timedelta(minutes=1)))
    assert [why for why, _ in wakes(here)] == ["queue", "queue"]


def test_no_queued_task_opens_while_the_terminal_cannot_say_which_sessions_live(
    tmp_path: Path,
) -> None:
    terminal = with_caller()
    terminal.unreadable = "agterm did not answer"
    here = here_of(tmp_path, terminal)
    made(here, "first", status="landed", since=LATER)
    made(here, status="queued", after=("first",), lead="builder")
    duty = duty_of(here, HOUR)
    queue.tick(duty)
    assert wakes(here) == []
    assert duty.kept.problems == {
        "sessions": "the board's look at the task sessions failed: agterm's sessions could "
        "not be read: agterm did not answer"
    }
    terminal.unreadable = None
    queue.tick(duty_of(here, HOUR, duty.kept))
    assert duty.kept.problems == {}
    assert wakes(here) == [("queue", None)]
