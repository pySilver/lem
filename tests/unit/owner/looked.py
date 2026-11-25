"""Records and looks for the cases of what waits: a task in a status with a hold, an open pull
request with its proposal, reads and refusal, and the look at its session."""

from datetime import timedelta
from typing import TYPE_CHECKING, Literal

from msgspec.structs import replace

from fakes.records import MOMENT, record
from lem.model.owner.looks import Look, Session, Stop
from lem.records.landing.merge import Merger, Refused
from lem.records.landing.propose import MergeRead, Proposed
from lem.records.landing.record import Landing, Pull
from lem.records.landing.review import Finding
from unit.landing.worlds import CHECKED, PROPOSED, REVIEWED, task

if TYPE_CHECKING:
    from lem.records.record import Record

type Verdict = Literal["merge", "call"]
type Source = Literal["github", "lem"]
type Kind = Literal["rule", "tip", "base", "target"]

TIP = "a" * 40
BASE = "b" * 40
TREE = "c" * 40
LATER = MOMENT + timedelta(minutes=30)


def look(slug: str = "gift-note", **fields: object) -> Look:
    """A look at a task `slug` with the task's `fields`, and nothing seen of the world."""
    return Look(record=record(slug, **fields))


def seen(found: Look, **fields: object) -> Look:
    """The look with `fields` of the world over it."""
    return replace(found, **fields)


def live(*, unanswered: bool = False) -> Session:
    return Session(live=True, since=MOMENT, unanswered=unanswered)


def gone() -> Session:
    return Session(live=False, since=MOMENT)


def stop(*, unread: bool = False) -> Stop:
    return Stop(at=LATER, unread=unread)


def proposed(*, green: bool = True, who: Merger = "merger") -> Proposed:
    reasons = () if green else ("the review left a must-fix",)
    return Proposed(
        tip=TIP,
        base=BASE,
        green=green,
        reasons=reasons,
        who_acts=who,
        at=MOMENT,
        contract=PROPOSED.contract,
    )


def read(
    verdict: Verdict | None, *, why: str = "Verdict: call. It needs you."
) -> MergeRead:
    return MergeRead(
        tip=TIP, base=BASE, base_tree=TREE, verdict=verdict, why=why, at=LATER
    )


def refused(source: Source, kind: Kind) -> Refused:
    return Refused(
        tip=TIP, source=source, kind=kind, line="the base moved", by="owner", at=MOMENT
    )


def opened(slug: str = "gift-note", **landing: object) -> Look:
    """An open task with a pull request and the landing's `landing` fields."""
    pull = Pull(number=44, url="https://github.com/o/r/pull/44", title="Gift note")
    proposal = landing.get("proposed")
    must = Finding(
        id="r1.1",
        level="must-fix",
        where="a.py",
        title="a defect",
        what="it",
        against="over",
    )
    findings = (must,) if isinstance(proposal, Proposed) and not proposal.green else ()
    made = Landing(
        phase="open",
        pull=pull,
        checked=replace(CHECKED, tip=TIP, base=BASE),
        reviews=(replace(REVIEWED, tip=TIP, findings=findings),),
    )
    found: Record = task("open")
    return Look(
        record=replace(
            found, task=replace(found.task, slug=slug), landing=replace(made, **landing)
        ),
    )
