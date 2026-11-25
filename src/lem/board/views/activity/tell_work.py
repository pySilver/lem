"""The feed's words of a span's start and end (`interview.start`, `interview.end`, `scout.start`,
`scout`, `builder.start`, `investigation` and the rest of `main`'s `SAYS`).

The end of a run of the checks and of a review is said by the run's own entry (`CheckEnd`,
`ReviewRound`), which holds its result, so their span's end is no row of its own.
"""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.board.views.activity import talk, told

if TYPE_CHECKING:
    from lem.records.journal.task import SpanMark
    from lem.records.task import Task
    from lem.records.work import Investigation

BUILDS = frozenset(("builder", "task", "small"))
START = "start"
# The fast track's one builder, by the job its span names.
FAST_JOB = "the small change"
STARTS = MappingProxyType(
    {
        "interview": told.Told(
            told.YOU,
            told.USER,
            "The interview started",
            "Lem asks you one question at a time",
        ),
        "scout": told.Told(
            told.LEAD,
            told.EYE,
            "The scout started",
            "it reads the code for the facts the criteria need",
        ),
        "lead": told.Told(told.LEAD, told.CODE, "The agent started"),
        "polish": told.Told(told.LEAD, told.CODE, "The polish pass started"),
        "checks": told.Told(told.GATE, "play", "The checks started"),
        "review": told.Told(told.GATE, told.EYE, "The review started"),
    }
)
ENDS = MappingProxyType(
    {
        "interview": told.Told(
            told.LEM,
            told.PAGE,
            "The interview’s questions ended",
            "Lem writes the criteria from the answers",
        ),
        "scout": told.Told(told.LEAD, told.PAGE, "The scout’s report is in"),
        "lead": told.Told(told.LEAD, told.CODE, "The agent ended"),
        "polish": told.Told(told.LEAD, told.CODE, "The polish pass ended"),
    }
)
# What the investigation found, as its end says it.
CALLS = MappingProxyType(
    {
        "small": "The investigation found a plain cause: the fast track fixes it",
        "full": "The investigation found a plain cause: the standard track",
        "not-a-bug": "The investigation found no bug",
        "not-reproduced": "The investigation did not reproduce the bug",
        "answer": "The investigation answered the question",
    }
)


def span(entry: SpanMark, task: Task) -> tuple[told.Told, ...]:
    """A span's mark in words; none for the end of the checks and of a review."""
    if entry.name in BUILDS:
        head = "A builder started" if entry.edge == START else "A builder ended"
        return (told.Told(told.LEAD, told.CODE, head, job_words(entry.job)),)
    if entry.name == "plan-talk":
        return (talked(entry, task),)
    if entry.name == "investigation":
        return (investigated(entry, task.investigation),)
    table = STARTS if entry.edge == START else ENDS
    known = table.get(entry.name)
    if known is None:
        return ()
    text = known.text or entry.job or ""
    return (told.Told(known.look, known.icon, known.head, text),)


def job_words(job: str | None) -> str:
    """A builder's job, the fast track's as "the change"."""
    return "the change" if job == FAST_JOB else job or ""


def talked(entry: SpanMark, task: Task) -> told.Told:
    """The plan talk's start with its reviewer, or its end with its record."""
    record = task.talk
    reviewer = entry.by or ""
    if not reviewer and record:
        reviewer = record.reviewer
    with_whom = f"with {reviewer}" if reviewer else ""
    if entry.edge == START:
        return told.Told(told.GATE, told.SPLIT, "The plan talk started", with_whom)
    if record is None:
        return told.Told(told.GATE, told.SPLIT, "The plan talk ended", with_whom)
    said = talk.counts(record)
    return told.Told(
        told.GATE, told.SPLIT, "The plan talk ended", f"{with_whom}: {said}"
    )


def investigated(entry: SpanMark, found: Investigation | None) -> told.Told:
    """The investigation's start, or its end with what it found."""
    if entry.edge == START:
        fix = found is not None and found.kind == "fix"
        does = "reproduces the bug and finds its cause" if fix else "finds the answer"
        return told.Told(
            told.LEAD, told.EYE, "The investigation started", f"an investigator {does}"
        )
    if found is None:
        return told.Told(told.DONE, told.EYE, "The investigation ended")
    head = CALLS.get(found.call or "", "The investigation ended")
    look = told.YOU if found.call == "not-reproduced" else told.DONE
    line = found.line or ""
    return told.Told(look, told.EYE, head, line, where(found))


def where(found: Investigation) -> str:
    """Where the investigation looked, and whether it reproduced the bug of a fix."""
    parts = [found.where or ""]
    if found.kind == "fix" and found.reproduced is not None:
        parts.append("reproduced" if found.reproduced else "not reproduced")
    return " · ".join(part for part in parts if part)
