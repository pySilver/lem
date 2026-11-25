"""The stages of a build (`stage_of` on `main`): an investigation, the fast track's change, or the
plan before its first task, each task of the plan by its span, and the build after the first
task where no task runs."""

import re
from typing import TYPE_CHECKING

from lem.board.views.timeline.shapes import Stage

if TYPE_CHECKING:
    from collections.abc import Iterator
    from datetime import datetime

    from lem.board.views.timeline.blocks import Block
    from lem.records.record import Record
    from lem.records.work import Span

PLAN = ("plan", "Plan", "Plan")
BUILD = ("build", "Build", "Build")
INVESTIGATION = ("investigation", "Investigation", "Inv.")
CHANGE = ("change", "The change", "Change")
JOB = re.compile(r"task (?P<number>\d+) of (?P<count>\d+)")


def building(record: Record, block: Block) -> Iterator[Stage]:
    """A build's stages."""
    task = record.task
    if task.investigation is None and task.lead != "small":
        tasks = [span for span in task.spans if span.name == "task"]
        yield from planned(tasks, block)
        return
    named = CHANGE if task.investigation is None else INVESTIGATION
    yield Stage(*named, block.start, block.end, live=block.live)


def planned(tasks: list[Span], block: Block) -> Iterator[Stage]:
    """The plan before its first task, each task, and the build after the first."""
    reach = block.start
    for span in tasks:
        start, end = clipped(span, block)
        if start >= end:
            continue
        if start > reach:
            yield gap(tasks, (reach, start), live=False)
        runs = block.live and span.end is None
        yield job_stage(span, start, end, live=runs)
        reach = end
    if reach < block.end:
        yield gap(tasks, (reach, block.end), live=block.live)


def gap(tasks: list[Span], piece: tuple[datetime, datetime], *, live: bool) -> Stage:
    """The plan before the first task began, the build between and after them."""
    start, end = piece
    began = bool(tasks) and start > tasks[0].start
    named = BUILD if began else PLAN
    return Stage(*named, start, end, live=live)


def clipped(span: Span, block: Block) -> tuple[datetime, datetime]:
    """The part of a task's span inside the build."""
    end = span.end or block.end
    return max(block.start, span.start), min(block.end, end)


def job_stage(span: Span, start: datetime, end: datetime, *, live: bool) -> Stage:
    """A task of the plan: `Task 2`, `T2`, `of 3`."""
    found = JOB.fullmatch(span.job or "")
    if found is None:
        return Stage("task", "A task of the plan", "Task", start, end, live=live)
    number = found["number"]
    sub = f"of {found['count']}"
    return Stage(
        f"task-{number}", f"Task {number}", f"T{number}", start, end, sub, live
    )
