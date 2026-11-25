"""The request and the criteria in the pull request's text (`main:land.pr_text`,
`criteria_lines`, `change_line`, `issue_line`): the owner's words, the issue it came from, the
track and why, each criterion with its case and what its tests gave, and each change of a
criterion during the build."""

from typing import TYPE_CHECKING

from lem.app.landing.pr_inputs import Block, Lines, block
from lem.model.landing.green_words import change_why, reason, taken_over
from lem.records.decisions import CriterionChanged
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.records.criterion import Criterion
    from lem.records.record import Record

PROVED = "passes on the branch, fails on the base commit"
UNKEPT = "(the owner's words were not kept for this task)"
NO_REASON = "no reason is on record"
CHANGED = "Criteria that changed during the build, in the order of the record:"


def request(record: Record) -> tuple[Block, ...]:
    """The request in the owner's words, and the line `Issue: #42` under it for a task from
    an issue of GitHub, which links the two both ways; no word that closes it."""
    words = record.task.ask.strip() or UNKEPT
    quoted = tuple(f"> {line}" for line in words.splitlines())
    ticket = record.task.ticket
    shown: Lines = ()
    if ticket is not None and ticket.tracker == "github" and ticket.id.startswith("#"):
        shown = (f"Issue: {ticket.id}",)
    return (Block(heading="## The request", lines=quoted), *block(None, shown))


def proved(record: Record, number: int) -> bool:
    """Whether the checks saw the criterion's tests fail on the base and pass on the tip."""
    checked = (record.landing or Landing()).checked
    runs = checked.criteria if checked else ()
    return any(
        run.criterion == number and run.red_on_base and run.green_on_tip for run in runs
    )


def criterion_lines(record: Record, criterion: Criterion) -> Lines:
    """One criterion: its sentence, the steps of its case, each test with what the check
    gave, or why it has none."""
    gave = PROVED if proved(record, criterion.number) else "not checked"
    steps = tuple(f"   {step}" for step in criterion.case)
    tests = tuple(f"   - `{test.command}`: {gave}" for test in criterion.tests)
    untested = (f"   - no test: {criterion.no_test}",) if criterion.no_test else ()
    return (f"{criterion.number}. {criterion.text}", *steps, *tests, *untested)


def change_line(record: Record, change: CriterionChanged) -> str:
    """One change of a criterion: what it was and is, why, who, and the approval of his
    that took it over."""
    was, now = (
        " ".join((change.was or "").split()),
        " ".join((change.now or "").split()),
    )
    said = f'was "{was}", now "{now}"'
    if change.how != "changed":
        said = f'added, "{now}"' if change.how == "added" else f'removed, was "{was}"'
    who = ""
    if change.decision is None:
        who = (
            " By the lead."
            if change.by == "lead"
            else f" By the personas: {change.said}"
        )
    later = taken_over(record, change)
    after = f" Approved by the owner afterwards (approval {later})." if later else ""
    return (
        f"- criterion {change.criterion}: {said}. {why_of(record, change)}.{who}{after}"
    )


def why_of(record: Record, change: CriterionChanged) -> str:
    """Why a criterion changed, without its own full stop."""
    return reason(change_why(record, change))


def listed(record: Record) -> Lines:
    """Each criterion with its lines, then each change of a criterion in the order of the
    record."""
    criteria = record.task.criteria.criteria
    lines = tuple(line for found in criteria for line in criterion_lines(record, found))
    changes = tuple(
        change_line(record, change)
        for change in record.task.decisions
        if isinstance(change, CriterionChanged)
    )
    return (*lines, *(("", CHANGED, "", *changes) if changes else ()))


def full(record: Record) -> tuple[Block, ...]:
    """The standard track's criteria, and the changes of the build under them."""
    why = record.task.criteria.why or NO_REASON
    lines = (f"The standard track, because {why}", "", *listed(record))
    return (Block(heading="## Acceptance criteria", lines=lines),)
