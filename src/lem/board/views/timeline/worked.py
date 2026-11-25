"""The stretches of a task's spans, each on the lane of who held the work (the stages of
`time_of` on `main` whose start is logged): the interview is yours, the scout, an investigation,
a builder and the polish pass are the builders', and the checks and the review their own lanes.
The agent's span is none of these: a build's states say what the agent did (`blocks.py`).

A plan talk is the review's, beside the work: it is no cover of a state's time.
"""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.board.views import words
from lem.board.views.activity import talk
from lem.board.views.activity.tell_work import FAST_JOB
from lem.board.views.timeline import frame, shapes

if TYPE_CHECKING:
    from collections.abc import Iterator

    from lem.records.task import Task
    from lem.records.work import Span

# Each span's lane, head and line; a builder's head is its job.
SPANS = MappingProxyType(
    {
        "interview": (
            shapes.YOU,
            "The interview",
            "Lem asks you one question at a time",
        ),
        "scout": (
            shapes.BUILDERS,
            "The scout reads the code",
            "for the facts the criteria need",
        ),
        "small": (
            shapes.BUILDERS,
            "One builder makes the change",
            "the fast track’s one builder",
        ),
        "polish": (shapes.BUILDERS, "The polish pass", "Lem’s pass over the change"),
        "checks": (shapes.CHECKS, "The checks", "the project’s checks on the branch"),
        "review": (shapes.REVIEW, "The review", "the review of the change"),
    }
)
BUILT = frozenset(("task", "builder"))
FIX = "an investigator reproduces the bug and finds its cause"
QUESTION = "an investigator finds the answer"


def worked(task: Task, drawn: frame.Frame) -> Iterator[frame.Drawn]:
    """The stretches of the task's spans but the agent's and the plan talk's."""
    for span in task.spans:
        said = said_of(task, span)
        if said is not None:
            lane, head, sub = said
            yield frame.ran(drawn, lane, span.start, span.end, (head, sub))


def said_of(task: Task, span: Span) -> tuple[str, str, str] | None:
    """A span's lane, head and line; None for the agent's and the plan talk's."""
    if span.name in BUILT:
        job = "the change" if span.job == FAST_JOB else span.job or "a job"
        return shapes.BUILDERS, words.capital(job), "a builder"
    if span.name == "investigation":
        found = task.investigation
        fix = found is not None and found.kind == "fix"
        return shapes.BUILDERS, "The investigation", FIX if fix else QUESTION
    return SPANS.get(span.name)


def talked(task: Task, drawn: frame.Frame) -> Iterator[frame.Drawn]:
    """The plan talk's stretches on the review's lane, with its record once it ended."""
    for span in task.spans:
        if span.name == "plan-talk":
            said = ("The plan talk", talk_sub(task, span))
            yield frame.ran(drawn, shapes.REVIEW, span.start, span.end, said)


def talk_sub(task: Task, span: Span) -> str:
    """With whom the plan talk ran, and its record once it ended, or that its record comes."""
    record = task.talk
    reviewer = span.by or ""
    if not reviewer and record is not None:
        reviewer = record.reviewer
    with_whom = f"with {reviewer}" if reviewer else ""
    if record is not None:
        counted = talk.counts(record)
        return f"{with_whom}: {counted}" if with_whom else counted
    if span.end is None:
        return f"{with_whom}; its record comes when the talk ends".lstrip("; ")
    return with_whom
