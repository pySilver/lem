"""Records of a task at its proposal for the cases of `green` and `propose`: a task on the
fast track or the standard track, each changed by the fields a case names, and the decisions,
reads and approvals as their writers keep them."""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Literal

from msgspec.structs import replace

from fakes.records import MOMENT
from lem.model.landing.propose_facts import Facts
from lem.records.approvals import Approval, ApprovedBy, PersonaRead, Silent
from lem.records.criteria import Criteria
from lem.records.criterion import Criterion, CriterionTest
from lem.records.decisions import Breaker, CriterionChanged, Level, Story, Taken
from lem.records.landing.checks import CriterionCheck
from lem.records.task import Shape
from lem.records.work import Span, SpanName
from unit.landing.worlds import CHECKED, PREPARED, task

if TYPE_CHECKING:
    from lem.records.record import Record

LATER = MOMENT + timedelta(hours=1)
TESTED = Criterion(
    number=1,
    text="The file holds the word y.",
    tests=(CriterionTest(command="sh tests/t.sh", files=("tests/t.sh",)),),
)
UNTESTED = Criterion(
    number=2, text="The file has one line.", no_test="printf ends every line so."
)
FULL_NOTES = (
    "## Decisions\n\nnone\n\n## Left open\n\nnone\n\n## Worth a look\n\nnone\n\n"
    "## Filed in the backlog\n\nnone\n\n## Not done\n\nnone\n"
)
STORY = Story(case=("1. One step.", "2. Another."), case_was="derived", cause="a split")


def approval(
    by: ApprovedBy = "owner", number: int = 1, at: datetime = LATER
) -> Approval:
    """An approval of the two criteria."""
    return Approval(
        number=number,
        at=at,
        by=by,
        size="full",
        why="the ticket names the word and the file",
        digest="d1",
        criteria=(TESTED, UNTESTED),
    )


def read(**fields: object) -> PersonaRead:
    """A read of the two criteria by two personas of two families, which ended at the
    moment."""
    made = PersonaRead(
        by="lem",
        started=MOMENT,
        ended=MOMENT,
        asked=2,
        answered=2,
        families=("opus", "sol"),
        criteria=2,
        digest="d1",
    )
    return replace(made, **fields)


QUIET = read(
    answered=0,
    families=(),
    silent=(Silent(name="the buyer, opus", why="the model was at capacity"),),
)


def full(**fields: object) -> Record:
    """A task on the standard track, its criteria read and approved by the owner, with its
    checks showing the tested criterion, and the task's `fields` over it."""
    made = task(
        **{
            **PREPARED,
            "checked": replace(CHECKED, criteria=(SHOWN,), criteria_digest="d1"),
        }
    )
    criteria = Criteria(
        size="full",
        why="the ticket names the word and the file",
        criteria=(TESTED, UNTESTED),
        digest="d1",
        approvals=(approval(),),
        reads=(read(),),
    )
    shape = Shape(type="feat", why="a word", track="full")
    task_fields = {"criteria": criteria, "shape": shape, **fields}
    return replace(made, task=replace(made.task, **task_fields))


def small(**fields: object) -> Record:
    """A task on the fast track with the task's `fields` over it."""
    made = task(**PREPARED)
    return replace(made, task=replace(made.task, **fields))


def with_landing(record: Record, **fields: object) -> Record:
    """The record with the landing's `fields` over it."""
    landing = record.landing
    assert landing is not None
    return replace(record, landing=replace(landing, **fields))


SHOWN = CriterionCheck(criterion=1, red_on_base=True, green_on_tip=True)
FACTS = Facts(notes=FULL_NOTES)


def picked(
    number: int, what: str, chose: str, by: Level = "dialectic", **more: object
) -> Taken:
    """A decision past the personas, with its story."""
    made = Taken(
        id=number,
        at=MOMENT,
        what=what,
        chose=chose,
        why="A reads first.",
        by=by,
        story=STORY,
    )
    return replace(made, **more)


def taken(number: int, what: str, chose: str, by: Level, **more: object) -> Taken:
    """A decision of the ladder."""
    made = Taken(id=number, at=MOMENT, what=what, chose=chose, why="it holds", by=by)
    return replace(made, **more)


def changed(
    number: int,
    how: Literal["changed", "added", "removed"],
    criterion: int,
    why: str,
    **more: object,
) -> CriterionChanged:
    """A change of an approved criterion."""
    made = CriterionChanged(
        id=number, at=MOMENT, how=how, criterion=criterion, why=why, approval=1
    )
    return replace(made, **more)


def breaker(
    number: int,
    cause: Literal["irreversible", "criteria"] = "criteria",
    **more: object,
) -> Breaker:
    """A stop of the build at the breaker."""
    made = Breaker(
        id=number,
        at=MOMENT,
        cause=cause,
        what="The note has no place that keeps criterion 1",
        document="breaker.md",
        handoff="handoff.md",
    )
    return replace(made, **more)


def span(name: SpanName, at: datetime = MOMENT) -> Span:
    """A span that began at `at`."""
    return Span(name=name, start=at)
