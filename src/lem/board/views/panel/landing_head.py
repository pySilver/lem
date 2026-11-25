"""The head of the large card of a task in its landing (`board_model.now_head`, `starts_landing`
and `step_runs` on `main`): the step that runs as its page says it, the start of a landing,
checks that ended without passing, or the checks and the review."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.records.journal.landing import CheckEnd

if TYPE_CHECKING:
    from lem.records.record import Record
    from lem.records.work import Span

# The step of a landing that runs, by its span.
RUNS = MappingProxyType(
    {
        "polish": "The polish pass runs",
        "checks": "The checks run",
        "review": "The review runs",
    }
)
STEPS = frozenset((*RUNS, "builder"))
# The head of checks that ended and stopped the landing, by their outcome.
ENDS = MappingProxyType(
    {
        "red": "The checks are red",
        "refused": "The checks refused the change",
        "stopped": "The checks were stopped",
    }
)


def landing(record: Record) -> str:
    """What the landing of the task does now."""
    step = running(record)
    if step is not None:
        job = step.job or "its job"
        return RUNS.get(step.name) or f"A builder makes {job}"
    if starts(record):
        return (
            "It starts its landing: the rebase onto the base, then the polish pass, "
            "before the checks"
        )
    ended = next(
        (one for one in reversed(record.journal) if isinstance(one, CheckEnd)), None
    )
    if ended is not None and ended.outcome in ENDS:
        return ENDS[ended.outcome]
    return "The checks and the review run on it"


def running(record: Record) -> Span | None:
    """The newest step of the landing that started and has not ended."""
    open_steps = [span for span in steps(record) if span.end is None]
    return open_steps[-1] if open_steps else None


def steps(record: Record) -> list[Span]:
    """The steps of the landing: the spans of its kinds since the task began to land."""
    since = record.task.since
    return [
        span for span in record.task.spans if span.name in STEPS and span.start >= since
    ]


def starts(record: Record) -> bool:
    """Whether the landing starts: no step and no run of the checks yet, and the polish
    pass to come off the fast track."""
    landing = record.landing
    began = landing is not None and (
        landing.checked is not None or landing.polished is not None
    )
    ended = any(isinstance(one, CheckEnd) for one in record.journal)
    small = record.task.criteria.size == "small"
    return not (began or ended or small or steps(record))
