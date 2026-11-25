"""What the investigation of a bug or of a question found, in the one form the landing and the
board read (`project.investigation_form` on `main`): its kind, the call that sets the next
path, one line (the cause, the answer, or what was tried), the cause's place, and for a fix
whether the bug was reproduced. Its record ends the investigation's span."""

from types import MappingProxyType
from typing import TYPE_CHECKING, Literal

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.task import holds, spans
from lem.records.base import Frozen
from lem.records.work import Investigation

if TYPE_CHECKING:
    from lem.records.base import Moment, TaskPath
    from lem.records.record import Record

type Kind = Literal["fix", "question"]
type Call = Literal["small", "full", "not-a-bug", "not-reproduced", "answer"]
type FoundKind = Literal["bug", "none", "question", "unreproduced"]

# The calls of each kind.
CALLS = MappingProxyType(
    {"fix": ("small", "full", "not-a-bug", "not-reproduced"), "question": ("answer",)}
)
UNREPRODUCED = "not-reproduced"
# The calls of a plain cause, which has a place.
PLAIN = frozenset(("small", "full"))
FACT = "the investigation waits for one more fact"
FORM = (
    "lem task investigated SLUG --kind fix|question --call CALL --line TEXT "
    "[--where PATH:SYMBOL] [--reproduced|--not-reproduced, for a fix]"
)


class Findings(Frozen, frozen=True, kw_only=True):
    """What the investigator's report says, as Lem writes it down after it read the report."""

    kind: Kind
    call: Call
    line: str
    found: FoundKind | None = None
    where: str | None = None
    reproduced: bool | None = None


def common_refusal(given: Findings) -> str | None:
    """Why the findings of either kind are not in their form, or None."""
    if given.call not in CALLS[given.kind]:
        return (
            "call is small, full, not-a-bug or not-reproduced for a fix, and answer for a "
            f"question; this one is {given.call!r} for a {given.kind}"
        )
    lines = given.line.splitlines()
    if len(lines) != 1 or not lines[0].strip():
        return "line is one line of text: the cause, the answer, or what was tried"
    if given.where is not None and not given.where.strip():
        return "where is the cause's file and symbol, as PATH:SYMBOL"
    return None


def question_refusal(given: Findings) -> str | None:
    """Why a question's findings say what only a fix's say, or None."""
    if given.reproduced is None:
        return None
    return (
        "reproduced is a fix's; the investigation of a question answers it and reproduces "
        "nothing"
    )


def fix_refusal(given: Findings) -> str | None:
    """Why a fix's findings, or a question's, break a rule of their kind, or None."""
    if given.kind != "fix":
        return question_refusal(given)
    if given.reproduced is None:
        return (
            "a fix's record says whether the bug was reproduced, with --reproduced or "
            "--not-reproduced"
        )
    if given.call in PLAIN and given.where is None:
        return "a plain cause has a place: where names the cause's file and symbol"
    if given.call == UNREPRODUCED and given.reproduced:
        return "not-reproduced is a bug that was not reproduced, and this record says it was"
    return None


def investigation(
    given: Findings, *, report: TaskPath | None, now: Moment
) -> Investigation:
    """The investigation's record from its findings, the report's path in the task's folder
    and the moment; refused when the findings are not in their form."""
    why = common_refusal(given) or fix_refusal(given)
    if why is not None:
        raise Refusal(
            "investigation",
            f"{FORM}: {why}",
            "write the record again in that form, from the investigator's report",
        )
    return Investigation(
        kind=given.kind,
        found=given.found,
        call=given.call,
        line=given.line.strip(),
        where=given.where,
        reproduced=given.reproduced,
        report=report,
        at=now,
    )


def investigated(record: Record, *, found: Investigation, now: Moment) -> Record:
    """The record with the investigation's findings, and its span ended when it is open; a
    bug that was not reproduced waits for one more fact from the owner, in the same write."""
    task = replace(record.task, investigation=found)
    written = spans.ended_if_open(replace(record, task=task), "investigation", now)
    if found.call != UNREPRODUCED:
        return written
    return holds.waiting(written, on="fact", line=FACT, now=now)
