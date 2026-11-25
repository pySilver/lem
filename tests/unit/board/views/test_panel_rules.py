"""The rules a task's panel holds beyond the afternoon's pictures (`main`'s
`test_board_model.py` Acts, Landing, Sessions): the acts the header offers, the step a landing's
large card names, and the header's "Open a session"."""

import dataclasses
from typing import TYPE_CHECKING

import msgspec

from fixtures.board.make import ran
from fixtures.board.moments import NOW, ago
from fixtures.board.receipt import SLUG
from fixtures.board.shown import VERSION, VIEWER, ZONE
from lem.app.sessions.phase import phase_or_none
from lem.board.views.panel import heads, opening
from lem.board.views.panel.panel import panel
from lem.board.views.rule import ENDED
from lem.board.views.world import Clock, Forge, Place, Seen, World
from lem.kernel import release
from lem.model.owner.looks import Session
from lem.records.record import Record
from lem.records.task import Task
from unit.board.views.afternoon import world

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.base import Moment

GIFT = "gift-note-in-export"
PLACE = Place(repo="shop", base="main", path="/work/shop")


def seen_of(status: str, *, spans: tuple = (), **beside: object) -> Seen:
    """A task `fix-the-login` of `status` since an hour ago, with what lies beside it."""
    task = Task(
        slug="fix-the-login",
        ask="fix the login",
        opened=ago(120),
        status=status,  # pyrefly: the fixture names a status of the record
        since=ago(60),
        spans=spans,
    )
    record = Record(release=release.running(), task=task)
    return Seen(record=record, **beside)


def alone(seen: Seen) -> World:
    """A workspace that holds the one task of `seen`."""
    return World(
        viewer=VIEWER,
        clock=Clock(now=NOW, zone=ZONE),
        version=VERSION,
        place=PLACE,
        tasks=(seen,),
    )


def session(*, live: bool, since: Moment | None = None) -> Session:
    """The task's newest session."""
    return Session(live=live, since=since or ago(90))


def test_a_merge_is_offered_while_open_and_not_while_the_forge_calls_it_conflicting(
    tmp_path: Path,
) -> None:
    """`main`'s `test_board_model.py`
    Acts.test_a_merge_is_offered_while_open_and_not_while_the_forge_calls_it_conflicting."""
    afternoon = world(tmp_path)
    head = panel(afternoon, SLUG, "overview").head
    assert head is not None
    assert head.acts is not None
    assert head.acts.merge is not None
    assert head.acts.merge.label == "Merge #44…"
    conflicting = dataclasses.replace(
        afternoon, forge=Forge(conflicts=frozenset((SLUG,)))
    )
    found = panel(conflicting, SLUG, "overview")
    assert found.head is not None
    assert found.head.acts is None
    step = panel(conflicting, SLUG, "merge")
    assert step.merge is None
    assert step.not_now is not None
    assert step.not_now.said.startswith("The forge calls its pull request conflicting")


def test_a_park_is_offered_while_a_breaker_waits_and_not_once_the_task_is_parked(
    tmp_path: Path,
) -> None:
    """`main`'s `test_board_model.py`
    Acts.test_a_park_is_offered_while_a_breaker_waits_and_not_once_the_task_is_parked."""
    afternoon = world(tmp_path)
    waits = panel(afternoon, GIFT, "park")
    assert waits.park is not None
    assert waits.park.confirm.eyebrow == "Park · breaker 1"
    parked = panel(afternoon, "fee-notice-to-merchants", "park")
    assert parked.park is None
    assert parked.not_now is not None
    assert parked.not_now.said.startswith(
        "Nothing to park: no breaker of this task waits for you."
    )


def test_criterion_1_a_landing_card_says_the_step_that_runs_as_its_page_does() -> None:
    """`main`'s `test_board_model.py`
    Landing.test_criterion_1_a_landing_card_says_the_step_that_runs_as_its_page_does: the
    large card's head names the step of the landing that runs."""
    repair = ran("builder", 50, 40, job="the repair of a conflict with the base")
    polish = seen_of("landing", spans=(repair, ran("polish", 39)))
    assert heads.now_head(polish) == "The polish pass runs"
    builder = seen_of("landing", spans=(ran("builder", 50, job=repair.job),))
    assert heads.now_head(builder) == (
        "A builder makes the repair of a conflict with the base"
    )
    ended = seen_of("landing", spans=(ran("polish", 50, 40),))
    assert heads.now_head(ended) == "The checks and the review run on it"
    assert heads.now_head(seen_of("landing")) == (
        "It starts its landing: the rebase onto the base, then the polish pass, before "
        "the checks"
    )


def test_a_task_whose_phase_needs_an_agent_and_has_no_live_session_gets_the_button() -> (
    None
):
    """`main`'s `test_board_model.py` Sessions.test_a_task_whose_phase_needs_an_agent_and_
    has_no_live_session_is_a_row_and_gets_the_button: the header's button (the row is the
    model's)."""
    gone = seen_of("building", session=session(live=False))
    head = panel(alone(gone), "fix-the-login", "overview").head
    assert head is not None
    assert head.acts is not None
    assert head.acts.session is not None
    assert head.acts.session.label == "Open a session"
    working = seen_of("building", session=session(live=True))
    found = panel(alone(working), "fix-the-login", "overview").head
    assert found is not None
    assert found.acts is None


def test_a_task_that_waits_only_for_his_merge_has_the_button() -> None:
    """`main`'s `test_board_model.py`
    Sessions.test_a_task_that_waits_only_for_his_merge_has_the_button_and_no_row: the
    header's button (the row is the model's)."""
    seen = seen_of("open", session=session(live=False))
    assert opening.opens(alone(seen), seen)


def test_the_board_offers_a_session_to_each_ended_task_that_phase_of_gives_one() -> None:
    """`main`'s `test_board_model.py`
    Sessions.test_the_board_offers_a_session_to_each_ended_task_that_phase_of_gives_one."""
    for status in sorted(ENDED):
        for worktree in (True, False):
            seen = seen_of(status, session=session(live=False), worktree=worktree)
            gets = phase_or_none(seen.record.task, worktree=worktree) is not None
            assert opening.opens(alone(seen), seen) is gets, (status, worktree)
    landed = seen_of("landed", session=session(live=False), worktree=True)
    assert opening.opens(alone(landed), landed)


def test_a_task_dropped_by_a_close_on_github_gets_the_button_only_while_its_worktree_stays() -> (
    None
):
    """`main`'s `test_board_model.py` Sessions.test_a_task_dropped_by_a_close_on_github_
    gets_the_button_only_while_its_worktree_stays."""
    stays = seen_of("dropped", session=session(live=False), worktree=True)
    assert opening.opens(alone(stays), stays)
    live = msgspec.structs.replace(stays, session=session(live=True))
    assert not opening.opens(alone(live), live)
    gone = msgspec.structs.replace(stays, worktree=False)
    assert not opening.opens(alone(gone), gone)
    unknown = msgspec.structs.replace(stays, session=None)
    assert not opening.opens(alone(unknown), unknown)
