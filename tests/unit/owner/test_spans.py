"""The spans in which a task ran without the owner, from his away and back and from a night's own
mark: the cases of `main`'s `tests/unit/test_owner.py::Spans`, as calls with records."""

from datetime import UTC, date, datetime
from unittest.mock import patch

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


def test_marks_after_a_task_ends_do_not_change_its_spans() -> None:
    task = record(opened=at(12), status="dropped", since=at(12, 3)).task
    assert spans.spans(task, presence(away(at(12, 4), "after the drop"))) == ()
    found = spans.spans(
        task,
        presence(away(at(12, 2), "before the drop"), back(at(12, 4), "after the drop")),
    )
    assert [(span.start, span.end) for span in found] == [(at(12, 2), None)]


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


def test_each_away_span_reuses_the_same_collection() -> None:
    task = record(opened=at(9)).task
    history = presence(
        away(at(10), "lunch"),
        back(at(11), "back"),
        away(at(15), "away"),
        back(at(17), "here"),
    )
    with patch.object(spans, "moved", wraps=spans.moved) as moved:
        found = spans.spans(task, history)
    collections = [call.args[0] for call in moved.call_args_list]
    assert len(collections) == len(history.changes)
    assert all(one is collections[0] for one in collections)
    assert isinstance(found, tuple)
    assert [(span.start, span.end) for span in found] == [
        (at(10), at(11)),
        (at(15), at(17)),
    ]
