"""Small makers of the afternoon's records: a span and its two marks, a move and its line, a
criterion, an approval, a command's run, so that each task's record reads as its story."""

from typing import TYPE_CHECKING

from fixtures.board.moments import ago
from lem.kernel import release
from lem.model.landing.world import Rules
from lem.records.approvals import Approval, PersonaRead
from lem.records.criterion import Criterion, CriterionTest
from lem.records.journal.task import SpanMark, StateNoted
from lem.records.landing.checks import Outcome
from lem.records.record import Record
from lem.records.work import Span

if TYPE_CHECKING:
    from lem.records.approvals import ApprovedBy, Size
    from lem.records.journal.entry import Entry
    from lem.records.landing.record import Landing
    from lem.records.task import Task
    from lem.records.work import SpanName

RULES = Rules(base="main", land="owner", commands=("make test", "make lint"))


def ran(
    name: SpanName,
    start: float,
    end: float | None = None,
    job: str | None = None,
) -> Span:
    """A span that began `start` minutes before now and ended `end` minutes before it, or
    runs."""
    return Span(
        name=name, job=job, start=ago(start), end=None if end is None else ago(end)
    )


def marks(spans: tuple[Span, ...]) -> tuple[SpanMark, ...]:
    """The journal's marks of each span: its start, and its end when it ended."""
    found: list[SpanMark] = []
    for each in spans:
        found.append(
            SpanMark(at=each.start, name=each.name, edge="start", job=each.job)
        )
        if each.end is not None:
            found.append(
                SpanMark(at=each.end, name=each.name, edge="end", job=each.job)
            )
    return tuple(found)


def moved(
    minutes: float, status: str, line: str | None = None, hold: str | None = None
) -> StateNoted:
    """A move of the task `minutes` before now, with the stage's line and the hold's kind."""
    return StateNoted(at=ago(minutes), status=status, hold=hold, line=line)


def journal(*entries: Entry) -> tuple[Entry, ...]:
    """The entries in the order of their moments; two of one moment keep their order."""
    return tuple(sorted(entries, key=lambda entry: entry.at))


def criterion(
    number: int, text: str, *steps: str, chart: str | None = None, test: str = ""
) -> Criterion:
    """A criterion with its case's steps, its chart, and the test that shows it (`sh FILE`)."""
    tests = (CriterionTest(command=f"sh {test}", files=(test,)),) if test else ()
    return Criterion(number=number, text=text, case=steps, chart=chart, tests=tests)


def approval(
    minutes: float,
    by: ApprovedBy,
    size: Size,
    criteria: tuple[Criterion, ...],
    why: str,
    digest: str,
) -> Approval:
    """Approval number 1, given `minutes` before now."""
    return Approval(
        number=1,
        at=ago(minutes),
        by=by,
        size=size,
        why=why,
        digest=digest,
        criteria=criteria,
    )


def read(
    start: float, end: float, criteria: int, digest: str, flagged: int = 0
) -> PersonaRead:
    """The personas' read of the criteria by Lem: three asked of two families, all answered."""
    return PersonaRead(
        by="lem",
        started=ago(start),
        ended=ago(end),
        asked=3,
        answered=3,
        families=("opus", "sol"),
        criteria=criteria,
        flagged=flagged,
        digest=digest,
    )


def output_of(number: int) -> str:
    """The path of the whole output of command `number` of the first round of the checks, as
    the checks publish it (`app/landing/checks_run.py`), with a made-up digest."""
    return f"checks/r1-{number}-{number:012x}.log"


def passed(command: str, last: str, number: int) -> Outcome:
    """A command of the checks that passed, with its whole output in the run's log file."""
    return Outcome(
        command=command,
        exit=0,
        last=last,
        output=output_of(number),
        passed=True,
    )


def record(task: Task, landing: Landing | None, entries: tuple[Entry, ...]) -> Record:
    """A task's record as the store wrote it once, on this release."""
    return Record(
        release=release.running(),
        revision=1,
        task=task,
        landing=landing,
        journal=entries,
    )
