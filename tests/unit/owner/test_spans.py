"""The spans in which a task ran without the owner, from his away and back and from a night's own
mark: the cases of `main`'s `tests/unit/test_owner.py::Spans`, as calls with records."""

from datetime import UTC, date, datetime

from fakes.records import record
from lem.model.owner import marks, spans
from lem.records.owner import Change, Presence

NIGHT = date(2026, 11, 19)


def at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 11, 19, hour, minute, tzinfo=UTC)


def presence(*changes: Change) -> Presence:
    return Presence(away=changes[-1].away, since=changes[-1].at, changes=changes)


def away(moment: datetime, words: str) -> Change:
    return Change(away=True, at=moment, words=words)


def back(moment: datetime, words: str) -> Change:
    return Change(away=False, at=moment, words=words)


def test_a_back_ends_his_away_and_never_a_night() -> None:
    task = record(opened=at(2), night=NIGHT, mode="alone", mode_since=at(2)).task
    found = spans.spans(
        task, presence(away(at(1), "I'm away"), back(at(2, 10), "/lem im-back"))
    )
    assert [(span.start, span.end) for span in found] == [(at(2), None)]


def test_a_day_task_runs_from_his_away_to_his_back() -> None:
    task = record(opened=at(14)).task
    found = spans.spans(
        task,
        presence(away(at(14, 5), "/lem im-away"), back(at(16, 30), "/lem im-back")),
    )
    said = [
        (span.start, span.end, span.started.words, span.ended and span.ended.words)
        for span in found
    ]
    assert said == [(at(14, 5), at(16, 30), "/lem im-away", "/lem im-back")]


def test_on_one_second_the_repository_comes_first_and_each_list_keeps_its_order() -> (
    None
):
    task = record(opened=at(14), night=NIGHT, mode="alone", mode_since=at(14, 5)).task
    found = marks.marks(
        task, presence(away(at(14, 5), "away"), back(at(14, 5), "back"))
    )
    assert [(mark.own, mark.away) for mark in found] == [
        (True, False),
        (False, True),
        (False, False),
    ]


def test_an_away_and_a_back_before_the_task_opened_are_no_span_of_it() -> None:
    task = record(opened=at(12)).task
    assert spans.spans(task, presence(away(at(10), "away"), back(at(11), "back"))) == ()


def test_a_task_opened_while_he_is_away_runs_without_him_from_its_open() -> None:
    task = record(opened=at(12)).task
    found = spans.spans(task, presence(away(at(10), "away")))
    assert [(span.start, span.end) for span in found] == [(at(12), None)]


def test_two_aways_of_one_day_task_are_two_spans() -> None:
    task = record(opened=at(9)).task
    found = spans.spans(
        task,
        presence(
            away(at(10), "lunch"),
            back(at(11), "back"),
            away(at(15), "away"),
            away(at(16), "still away"),
            back(at(17), "here"),
        ),
    )
    assert [(span.start, span.end, span.started.words) for span in found] == [
        (at(10), at(11), "lunch"),
        (at(15), at(17), "away"),
    ]
