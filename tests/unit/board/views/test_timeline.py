"""The card Where the time went of a task's Timeline (`board_model.time_of`, `time_rows`,
`time_shares` and `board_task.time_card` on `main`): a lane for each who held the work, the
stages as bands behind them, the moments on the lanes, the shares on the legend, and the axis."""

from datetime import timedelta
from typing import TYPE_CHECKING

from lem.board.views.timeline import view
from lem.records.approvals import Approval, PersonaRead
from lem.records.criteria import Criteria
from lem.records.journal.task import StateNoted
from lem.records.work import Span
from unit.board.views.afternoon import world as afternoon
from unit.board.views.timed import at, seen, task, world

if TYPE_CHECKING:
    from pathlib import Path

    from lem.board.inputs.task.timeline import Time, Track
    from lem.records.record import Record


def lanes(time: Time) -> dict[str, Track]:
    """The card's lanes by key."""
    return {track.key: track for track in time.tracks}


def card(made: Record, now: str = "13:00") -> Time:
    """The time card of the task `made` at `now`."""
    shown = view.timeline(world(seen(made), now=now), "gift-note")
    assert shown.time is not None
    return shown.time


def test_the_receipts_card_draws_who_held_its_work_over_its_stages(
    tmp_path: Path,
) -> None:
    shown = view.timeline(afternoon(tmp_path), "refund-line-on-receipt")
    time = shown.time
    assert time is not None
    assert (time.look, time.whole, time.over, time.day, time.dated) == (
        "you",
        "10h 10m in all",
        None,
        "today",
        False,
    )
    assert [(band.short, band.head, band.sub) for band in time.bands] == [
        ("Criteria", "Acceptance criteria", None),
        ("Plan", "Plan", None),
        ("T1", "Task 1", "of 2"),
        ("Build", "Build", None),
        ("T2", "Task 2", "of 2"),
        ("Checks", "Checks and review", None),
        ("PR", "Pull request", None),
    ]
    assert (time.bands[1].odd, time.bands[-1].now, time.bands[-1].end) == (
        True,
        True,
        None,
    )
    assert [track.key for track in time.tracks] == [
        "you",
        "lem",
        "lead",
        "builders",
        "checks",
        "review",
        "merger",
    ]
    held = lanes(time)
    assert (held["you"].held, held["you"].held_title) == (
        "7h 37m · 75%",
        "You held the work for 7h 37m of the task’s 10h 10m",
    )
    assert held["merger"].held is None
    builders = [spell.head for spell in held["builders"].spells]
    assert builders == ["The builders · Task 1 of 2", "The builders · Task 2 of 2"]
    passed = held["checks"].marks[0]
    assert (passed.head, passed.sub) == (
        "The checks · The checks passed",
        "The checks passed: make test, make lint",
    )
    merge = held["you"].spells[-1]
    assert (merge.head, merge.live, merge.end) == (
        "You · It waits for your merge",
        True,
        None,
    )
    assert round(merge.left + merge.width, 3) == time.now


def test_a_breaker_holds_the_task_for_the_owner_while_the_agents_span_runs(
    tmp_path: Path,
) -> None:
    time = view.timeline(afternoon(tmp_path), "gift-note-in-export").time
    assert time is not None
    yours = {spell.head: spell for spell in lanes(time)["you"].spells}
    assert yours["You · The build stopped: its breaker waits for you"].live
    # each move of the build is the agent's where no builder holds the work: it plans the
    # task before its first builder, and reads the report after one
    assert [spell.head for spell in lanes(time)["lead"].spells] == [
        "The agent · It plans the task",
        "The agent · It plans the task",
        "The agent · It reads the builder’s report",
    ]
    # and the breaker's wait stays in the stage the task was in
    assert [band.short for band in time.bands][-2:] == ["Build", "T2"]


def interviewed() -> Record:
    """A task whose interview ran from 10:00 to 10:20, whose personas read the criteria from
    10:25 to 10:30, and that the owner approved at 10:40 and Lem built from 10:41 to 11:00."""
    read = PersonaRead(
        by="lem",
        started=at("10:25"),
        ended=at("10:30"),
        asked=3,
        answered=3,
        families=("opus", "sol"),
        flagged=1,
    )
    approved = Approval(
        number=1,
        at=at("10:40"),
        by="owner",
        size="full",
        why="",
        digest="d",
        criteria=(),
    )
    return task(
        StateNoted(
            at=at("10:00"), status="shaping", hold="owner", line="the interview"
        ),
        StateNoted(at=at("10:41"), status="building", line="lead: builder"),
        StateNoted(at=at("11:00"), status="dropped", line="the owner dropped it"),
        status="dropped",
        opened=at("10:00"),
        spans=(Span(name="interview", start=at("10:00"), end=at("10:20")),),
        criteria=Criteria(approvals=(approved,), reads=(read,)),
    )


def test_lem_writes_the_criteria_after_the_interview_and_they_wait_for_his_yes_after_the_read() -> (
    None
):
    time = card(interviewed())
    held = lanes(time)
    assert [(spell.head, spell.sub) for spell in held["lem"].spells] == [
        (
            "Lem · Lem writes the criteria",
            "from your answers and what the code says",
        ),
    ]
    writes = held["lem"].spells[0]
    assert (writes.start, writes.end) == (at("10:20"), at("10:25"))
    waits = next(
        spell
        for spell in held["you"].spells
        if spell.head == "You · The criteria waited for your yes"
    )
    assert (waits.start, waits.end, waits.sub) == (
        at("10:30"),
        at("10:40"),
        "from the personas’ read to your approval · the read found a doubt",
    )
    read = held["personas"].spells[0]
    assert read.sub == "3 of 3 answered, two model families · 1 flagged"
    # an ended task has no line of now, and its stages end where it ended
    assert (time.now, time.bands[-1].end) == (None, at("11:00"))


def test_a_span_with_no_end_in_an_ended_task_is_a_moment_where_it_began() -> None:
    made = task(
        StateNoted(at=at("10:00"), status="building", line="lead: builder"),
        StateNoted(at=at("10:30"), status="dropped"),
        status="dropped",
        opened=at("10:00"),
        spans=(Span(name="task", job="task 1 of 2", start=at("10:05")),),
    )
    marks = lanes(card(made))["builders"].marks
    assert [(mark.head, mark.sub, mark.at) for mark in marks] == [
        ("The builders · Task 1 of 2: its start", "no record of its end", at("10:05")),
    ]


def test_the_shares_say_when_two_lanes_held_the_same_minutes() -> None:
    made = task(
        StateNoted(at=at("10:00"), status="building", line="lead: session"),
        status="building",
        opened=at("10:00"),
        spans=(Span(name="plan-talk", start=at("10:10")),),
    )
    time = card(made, now="11:00")
    held = lanes(time)
    assert (held["lead"].held, held["review"].held) == ("1h 00m · 100%", "50m · 83%")
    assert (
        time.over == "the shares add up to 183%, as two rows can hold the same minutes"
    )
    talk = held["review"].spells[0]
    assert (talk.head, talk.sub, talk.live) == (
        "The review · The plan talk",
        "its record comes when the talk ends",
        True,
    )


def test_two_stretches_of_one_lane_at_one_moment_keep_ids_of_their_own() -> None:
    made = task(
        StateNoted(at=at("10:00"), status="building", line="lead: builder"),
        StateNoted(at=at("10:30"), status="dropped"),
        status="dropped",
        opened=at("10:00"),
        spans=(
            Span(name="builder", job="the docs", start=at("10:05"), end=at("10:10")),
            Span(name="builder", job="the tests", start=at("10:05"), end=at("10:20")),
        ),
    )
    ids = [spell.id for spell in lanes(card(made))["builders"].spells]
    assert ids == ["ts-builders-1795341900000-1", "ts-builders-1795341900000-2"]


def test_a_tick_past_midnight_names_its_date() -> None:
    made = task(
        StateNoted(at=at("22:00"), status="building", line="lead: builder"),
        StateNoted(at=at("23:00") + timedelta(hours=3), status="dropped"),
        status="dropped",
        opened=at("22:00"),
    )
    time = card(made, now="23:00")
    assert time.dated
    # four hours from 22:00, in ticks of 40 minutes
    assert [(tick.date, tick.clock) for tick in time.ticks][2:4] == [
        (None, "23:20"),
        ("Nov 23", "00:00"),
    ]
