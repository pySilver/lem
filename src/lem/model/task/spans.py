"""The spans of a task's time card: the start and the end of each, as `Task.spans` and the
journal keep them (`project.start_form` and `TASK_JOB` on `main`).

Each stage marks its start and its end as they happen, so that the time card has exact moments
(the owner's pick of 2026-11-17). A span is told apart by its name, and a task of the plan and a
builder's job by their job too, since two builders may run at one time.
"""

import re
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.task import span_forms as forms
from lem.model.task import span_marks as marks
from lem.records.work import Span

if TYPE_CHECKING:
    from lem.records.base import Moment
    from lem.records.record import Record
    from lem.records.task import Task

type Spans = tuple[Span, ...]
# The spans whose job tells one from another of the same name.
KEYED = frozenset(("task", "builder"))
OF = re.compile(r"([1-9][0-9]*)/([1-9][0-9]*)")


def job_of(given: forms.Given) -> str | None:
    """The span's job as the record keeps it: `task N of M` for a task of the plan, the
    builder's or the investigation's job as given; refused when its fields are not its form."""
    form = forms.form_of(given.name)
    forms.check(form, given, at_end=given.edge == "end")
    if given.of is None:
        return given.job
    found = OF.fullmatch(given.of)
    if found is None:
        detail = f"--of is {given.of!r}: N and M are whole numbers, 1 or more"
        raise forms.refused(form.says, given, detail)
    return f"task {found[1]} of {found[2]}"


def open_at(spans: Spans, name: str, job: str | None) -> int | None:
    """The place of the open span `name` (of `job`, for a keyed span), or None."""
    keyed = name in KEYED
    found = (
        at
        for at, span in enumerate(spans)
        if marks.is_open(span, name, job, keyed=keyed)
    )
    return next(found, None)


def led(task: Task, given: forms.Given) -> Task:
    """The task with the lead a span's start names: the fast track's builder (`small`), or a
    lead's kind (`lead --by builder|session`)."""
    if given.name == "small":
        return replace(task, lead="small")
    if given.by == "builder":
        return replace(task, lead="builder")
    if given.by == "session":
        return replace(task, lead="session")
    return task


def started(record: Record, given: forms.Given, now: Moment) -> Record:
    """The record with the span begun at `now`; a second start of an open span is refused.
    The start of a lead or of the fast track's builder names the task's lead too."""
    job = job_of(given)
    task = record.task
    if open_at(task.spans, given.name, job) is not None:
        named = " ".join(word for word in (given.name, job) if word)
        raise Refusal(
            "span-open",
            f"the span {named} of {task.slug} is open: it was started and has not ended",
            f"lem task span {task.slug} {given.name} end, with its field, ends it first",
        )
    name = forms.form_of(given.name).name
    span = Span(name=name, job=job, by=given.by, start=now)
    task = replace(task, spans=(*task.spans, span))
    if given.name in {"lead", "small"}:
        task = led(task, given)
    return marks.journaled(record, task, marks.mark_of(span, "start", now))


def closed(record: Record, at: int, now: Moment) -> Record:
    """The record with the span at `at` ended at `now`, and its mark in the journal."""
    spans = record.task.spans
    span = replace(spans[at], end=now)
    before = spans[:at]
    after = spans[at + 1 :]
    task = replace(record.task, spans=(*before, span, *after))
    return marks.journaled(record, task, marks.mark_of(span, "end", now))


def marked(record: Record, *, given: forms.Given, now: Moment) -> Record:
    """The record with the start or the end of a span, the change `lem task span` writes; an
    end with no open span of its name is refused."""
    if given.edge == "start":
        return started(record, given, now)
    at = open_at(record.task.spans, given.name, job_of(given))
    if at is None:
        slug = record.task.slug
        raise Refusal(
            "no-open-span",
            f"{slug} has no open span {given.name} to end",
            f"lem task span {slug} {given.name} start marks its start first",
        )
    return closed(record, at, now)


def ended_if_open(record: Record, name: str, now: Moment) -> Record:
    """The record with the open span `name` ended at `now`, as the record of its stage ends
    it (the investigation's, the plan talk's); the record as it is when none is open."""
    at = open_at(record.task.spans, name, None)
    return record if at is None else closed(record, at, now)
