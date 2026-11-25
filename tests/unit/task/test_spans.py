"""The spans of a task's time card: the form of each start and end, the record of each mark at
its exact moment, the open span a second start refuses and an end needs, and the spans a resumed
task takes with it (`StartForm` and `InterviewEvents` of `main`)."""

from datetime import timedelta
from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from fakes.command import lem
from fakes.records import MOMENT, record
from lem.app.tasks import spans as marking
from lem.kernel.errors import Refusal
from lem.model.task import span_marks, spans
from lem.model.task.span_forms import Given
from lem.records.journal.task import SpanMark
from unit.task import spaces

if TYPE_CHECKING:
    from pathlib import Path

    from lem.model.task.span_forms import Edge
    from lem.records.record import Record

LATER = MOMENT + timedelta(minutes=7)
SLUG = "fix-the-login"


def mark(before: Record, name: str, edge: Edge = "start", /, **fields: str) -> Record:
    """The record after one mark at MOMENT (a start) or LATER (an end)."""
    now = MOMENT if edge == "start" else LATER
    given = Given(
        name=name,
        edge=edge,
        of=fields.get("of"),
        job=fields.get("job"),
        by=fields.get("by"),
    )
    return spans.marked(before, given=given, now=now)


def refused(name: str, edge: Edge = "start", /, **fields: str) -> Refusal:
    """The refusal of one mark on a task that has none open."""
    with pytest.raises(Refusal) as caught:
        mark(record(SLUG, status="building"), name, edge, **fields)
    return caught.value


# The builder's jobs of `main` (`project.BUILDER_JOBS`) but "the small change", which is the span
# `small` now; written here, so that a job the rule drops fails this case.
BUILDER_JOBS = (
    "the repair of a conflict with the base",
    "the repair of a failed check",
    "the fix of a review's findings",
    "the removal of the task's item",
)


def test_each_start_in_its_form_and_its_end() -> None:
    forms = (
        ("lead", {"by": "builder"}, {}),
        ("lead", {"by": "session"}, {}),
        ("small", {}, {}),
        ("task", {"of": "2/3"}, {"of": "2/3"}),
        ("interview", {}, {}),
        ("scout", {}, {}),
        ("investigation", {"job": "fix"}, {}),
        ("investigation", {"job": "question"}, {}),
        ("plan-talk", {"by": "codex"}, {}),
        *(("builder", {"job": job}, {"job": job}) for job in BUILDER_JOBS),
    )
    for name, start, end in forms:
        begun = mark(record(SLUG, status="building"), name, **start)
        done = mark(begun, name, "end", **end)
        (span,) = done.task.spans
        assert (span.name, span.start, span.end) == (name, MOMENT, LATER), name
        assert [
            entry.edge for entry in done.journal if isinstance(entry, SpanMark)
        ] == [
            "start",
            "end",
        ]


def test_the_time_card_gets_exact_start_and_end_times() -> None:
    begun = mark(record(SLUG), "task", of="2/5")
    (span,) = begun.task.spans
    assert (span.job, span.start, span.end) == ("task 2 of 5", MOMENT, None)
    done = mark(begun, "task", "end", of="2/5")
    marks = [entry for entry in done.journal if isinstance(entry, SpanMark)]
    assert [(entry.at, entry.edge, entry.job) for entry in marks] == [
        (MOMENT, "start", "task 2 of 5"),
        (LATER, "end", "task 2 of 5"),
    ]


def test_a_start_that_takes_nothing_with_a_field() -> None:
    found = refused("interview", by="lem")
    assert found.code == "span-form"
    assert "the span interview takes nothing; this one has --by" in found.why
    assert "lem task span SLUG interview start" in found.fix


def test_the_interviews_end_takes_nothing_and_a_field_is_refused() -> None:
    begun = mark(record(SLUG, status="shaping"), "interview")
    done = mark(begun, "interview", "end")
    assert done.task.spans[0].end == LATER
    for field in ({"by": "lem"}, {"job": "y"}):
        with pytest.raises(Refusal) as caught:
            mark(begun, "interview", "end", **field)
        assert "the end of the span interview takes nothing; this one has" in (
            caught.value.why
        )


def test_a_start_without_its_field() -> None:
    assert refused("task").why == (
        "the span task, a task of the plan, takes --of N/M, and nothing else; this one "
        "has no field"
    )
    assert "this one has no field" in refused("plan-talk").why


def test_a_value_the_field_does_not_have() -> None:
    assert "--by is 'owner'" in refused("lead", by="owner").why
    assert "--job is 'bug'" in refused("investigation", job="bug").why
    assert "--by is ' '" in refused("plan-talk", by=" ").why


def test_another_field_in_place_of_its_own() -> None:
    found = refused("investigation", by="question")
    assert "takes --job fix|question, and nothing else; this one has --by" in found.why


def test_a_job_no_builder_has() -> None:
    found = refused("builder", job="the polish pass")
    assert "the span builder takes --job JOB" in found.why
    assert "the polish pass is lem land's" in found.why
    assert "--job is 'the polish pass'" in found.why
    small = refused("builder", job="the small change")
    assert "the fast track's builder is the span small" in small.why


def test_a_count_below_one_or_no_number() -> None:
    for given in ("0/3", "2/0", "two/3", "2", "-1/3"):
        assert f"--of is {given!r}: N and M are whole numbers, 1 or more" in (
            refused("task", of=given).why
        ), given


def test_the_landings_spans_are_lem_lands_own() -> None:
    for name in ("polish", "checks", "review"):
        found = refused(name)
        assert found.code == "span-landing"
        assert f"the span {name} is the landing's" in found.why
    assert refused("lunch").code == "span-name"


def test_a_second_start_of_an_open_span_is_refused() -> None:
    begun = mark(record(SLUG), "interview")
    with pytest.raises(Refusal) as caught:
        mark(begun, "interview")
    assert caught.value.code == "span-open"
    assert caught.value.fix.startswith(f"lem task span {SLUG} interview end")
    again = mark(mark(begun, "interview", "end"), "interview")
    assert [span.end for span in again.task.spans] == [LATER, None]


def test_two_tasks_of_the_plan_run_at_once_and_each_ends_by_its_own_of() -> None:
    both = mark(mark(record(SLUG), "task", of="1/2"), "task", of="2/2")
    second = mark(both, "task", "end", of="2/2")
    assert [(span.job, span.end) for span in second.task.spans] == [
        ("task 1 of 2", None),
        ("task 2 of 2", LATER),
    ]
    with pytest.raises(Refusal) as caught:
        mark(second, "task", "end", of="2/2")
    assert caught.value.code == "no-open-span"
    with pytest.raises(Refusal) as unnamed:
        mark(second, "task", "end")
    assert "the end of the span task takes --of" in unnamed.value.why


def test_an_end_needs_an_open_span() -> None:
    found = refused("scout", "end")
    assert found.code == "no-open-span"
    assert found.fix == f"lem task span {SLUG} scout start marks its start first"


def test_the_start_of_a_lead_or_the_fast_tracks_builder_names_the_lead() -> None:
    assert mark(record(SLUG), "lead", by="session").task.lead == "session"
    assert mark(record(SLUG), "lead", by="builder").task.lead == "builder"
    assert mark(record(SLUG), "small").task.lead == "small"
    assert mark(record(SLUG, lead="builder"), "scout").task.lead == "builder"


def test_a_record_of_its_stage_ends_its_span_and_none_open_changes_nothing() -> None:
    begun = mark(record(SLUG), "investigation", job="fix")
    assert spans.ended_if_open(begun, "investigation", LATER).task.spans[0].end == LATER
    plain = record(SLUG)
    assert spans.ended_if_open(plain, "plan-talk", LATER) is plain


def test_a_resumed_task_takes_the_spans_of_the_stages_before_the_build() -> None:
    marked = record(SLUG)
    for name, start, end in (
        ("interview", {}, {}),
        ("scout", {}, {}),
        ("investigation", {"job": "fix"}, {}),
        ("plan-talk", {"by": "codex"}, {}),
        ("task", {"of": "1/1"}, {"of": "1/1"}),
    ):
        marked = mark(mark(marked, name, **start), name, "end", **end)
    open_scout = mark(marked, "lead", by="builder")
    carried = span_marks.carried(open_scout.task.spans)
    assert [span.name for span in carried] == [
        "interview",
        "scout",
        "investigation",
        "plan-talk",
    ]
    assert span_marks.carried((replace(carried[0], end=None),)) == ()


def test_the_command_marks_a_span_on_the_tasks_record(tmp_path: Path) -> None:
    where = spaces.workspace(tmp_path / "repo")
    spaces.made(where, SLUG, status="building")
    start = Given(name="task", edge="start", of="1/3")
    written = marking.marked(where.state, SLUG, start)
    assert (written.job, written.edge) == ("task 1 of 3", "start")
    ran = lem("task", "span", SLUG, "task", "end", "--of", "1/3", cwd=where.checkout)
    assert ran.code == 0, ran.stderr
    result = ran.result()
    assert isinstance(result, dict)
    assert result | {"at": None} == {
        "slug": SLUG,
        "name": "task",
        "edge": "end",
        "job": "task 1 of 3",
        "at": None,
    }
    (span,) = spaces.read(where, SLUG).task.spans
    assert span.end is not None
    assert span.start == written.at
    wrong = lem("task", "span", SLUG, "task", "middle", cwd=where.checkout)
    assert wrong.code == 2
