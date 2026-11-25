"""The phase of a task's session, from its record, and the tasks that get none."""

from typing import TYPE_CHECKING, Any

import pytest

from fakes.records import MOMENT, record
from lem.app.sessions.phase import phase_of
from lem.kernel.errors import Refusal
from lem.records.holds import Blocked, BreakerHold, OwnerHold, Parked, ReleaseHold
from lem.records.task import Shape

if TYPE_CHECKING:
    from lem.records.holds import Hold

SMALL = Shape(type="fix", why="a typo", track="small")
FULL = Shape(type="feat", why="a column", track="full")
INTERVIEW = OwnerHold(on="interview", line="the interview waits", since=MOMENT)


@pytest.mark.parametrize(
    ("status", "hold", "fields", "worktree", "phase"),
    [
        ("shaping", None, {}, False, "shape"),
        ("queued", None, {}, False, "shape"),
        ("queued", None, {"lead": "builder"}, False, "build"),
        ("building", None, {"shape": FULL}, True, "build"),
        ("planned", None, {}, True, "build"),
        ("ready", None, {}, True, "land"),
        ("landing", None, {}, True, "land"),
        ("open", None, {}, True, "land"),
        ("building", None, {"shape": SMALL}, True, "fast"),
        ("open", None, {"shape": SMALL}, True, "fast"),
        ("shaping", INTERVIEW, {"shape": SMALL}, False, "shape"),
        ("building", INTERVIEW, {}, True, "shape"),
        ("planned", OwnerHold(on="plan", line="x", since=MOMENT), {}, True, "build"),
        ("building", BreakerHold(number=1, since=MOMENT), {}, True, "build"),
        (
            "landing",
            Blocked(why="red", fix="f", seat="merger", since=MOMENT),
            {},
            True,
            "land",
        ),
        ("landed", None, {}, True, "land"),
        ("dropped", None, {"shape": SMALL}, True, "fast"),
    ],
)
def test_the_record_gives_the_phase(
    *,
    status: str,
    hold: Hold | None,
    fields: dict[str, Any],
    worktree: bool,
    phase: str,
) -> None:
    made = record(status=status, hold=hold, **fields).task
    assert phase_of(made, worktree=worktree) == phase


@pytest.mark.parametrize(
    ("status", "hold", "worktree", "code"),
    [
        ("building", Parked(since=MOMENT), True, "parked"),
        (
            "building",
            ReleaseHold(began="0.1.0", running="0.3.0", say="two back", since=MOMENT),
            True,
            "release",
        ),
        ("landed", None, False, "ended"),
        ("answered", None, True, "ended"),
        ("dropped", None, False, "ended"),
    ],
)
def test_a_task_that_gets_no_session_is_refused_with_the_way_on(
    *, status: str, hold: Hold | None, worktree: bool, code: str
) -> None:
    made = record(status=status, hold=hold).task
    with pytest.raises(Refusal) as refused:
        phase_of(made, worktree=worktree)
    assert refused.value.code == code
    assert refused.value.fix
