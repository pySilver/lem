"""The owner's change of the criteria that wait for his yes, on the standard track
(`criteria.cmd_typed`, `cmd_change`, `cmd_unchanged` and `waits_for_change` on `main`).

His change is never his yes: his No comes first, typed in the task's session or on the board, and
the first answer counts. The change keeps the text he answered and asks his yes again under a new
question; a No whose note changes no criterion (a direction, a question) asks again of the same
text. Once the standard track has an approval, a criterion changes through its record instead
(`lem decisions criterion`).
"""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.criteria import pairs, waits
from lem.records.questions import Answer

if TYPE_CHECKING:
    from datetime import datetime

    from lem.model.criteria.read import Sheet
    from lem.records.approvals import Size
    from lem.records.criteria import Change
    from lem.records.task import Task

FIRST = "answered-first"
TAKE = "take that answer, and say in one line which answer was taken and from where"


def changeable(task: Task, size: Size | None) -> Refusal | None:
    """Why the criteria of `task`, whose file says `size`, take no change from his note now:
    they wait for no yes, an approval came after the wait began, the standard track has an
    approval, or the task is on the fast track."""
    slug, hold = task.slug, waits.hold_of(task)
    approvals = task.criteria.approvals
    kept = approvals[-1] if approvals else None
    if hold is None:
        return Refusal(
            "not-waiting",
            f"the criteria of {slug} do not wait for the owner's yes",
            "a change from his note is made while the interview's criteria, or a wait of "
            "the criteria, are held for his yes",
        )
    if kept is not None and kept.at >= hold.since:
        return Refusal(
            FIRST,
            f"approval {kept.number} (by {kept.by}, at {kept.at}) came after the wait he "
            "answered, and the first answer counts: nothing was changed",
            f"the task goes on from that approval; {TAKE}",
        )
    if kept is not None and kept.size == "full":
        return Refusal(
            "approved",
            f"{slug} has approval {kept.number} of its criteria on the standard track",
            f"a criterion changes through its record: lem decisions criterion {slug} "
            "--changed N --was TEXT --now TEXT",
        )
    if size == "small":
        return Refusal(
            "fast-track",
            f"{slug} is on the fast track",
            "the owner's change of its one criterion goes into criteria.md in his words "
            '(stages/new.md, "The fast track")',
        )
    return None


def typed(task: Task, now: datetime, words: str) -> Task:
    """The task with his No typed in its session, as the answer to the wait that stands;
    refused when an answer of the board came first. His own typed No again is no change."""
    question = waits.question_of(task) or waits.question(task, now, None)
    answer = question.answer
    if answer is None:
        said = Answer(option="no", label="No", note=words, source="session", at=now)
        return waits.answered(task, question, said)
    if answer.option == waits.SAID_NO and answer.source == "session":
        return task
    raise first(answer)


def first(answer: Answer) -> Refusal:
    """The refusal of a change that an answer of his came before."""
    return Refusal(
        FIRST,
        f"the owner's answer {answer.label!r} to this wait came first, on the "
        f"{answer.source} at {answer.at}: nothing was changed",
        TAKE,
    )


def no_first(task: Task) -> None:
    """Refuse a change when his answer to the wait that stands is not a No."""
    question = waits.question_of(task)
    said = question.answer if question else None
    if said is not None and said.option != waits.SAID_NO:
        raise first(said)


def changed(
    task: Task, *, sides: tuple[Sheet, Sheet], change: Change, shown: str
) -> Task:
    """The task whose criteria changed from the first of `sides` to the second by his note,
    waiting for his yes again on the file of mark `shown`; `change` holds his words, the text
    he answered and the marks of both sides."""
    no_first(task)
    before, after = sides
    if before.size != "full" or after.size != "full":
        raise Refusal(
            "not-full",
            "a change from the owner's note keeps the standard track, and these criteria "
            "say Size: small",
            "write Size: full, because WHY; the fast track's one criterion takes his change "
            "in his words",
        )
    found = pairs.pairs(before.criteria, after.criteria)
    if not found:
        raise Refusal(
            "unchanged",
            "the file has the same criteria as the ones the owner answered",
            "write each criterion his note changes in your words, with a concrete example; "
            f"a note that changes no criterion asks again: lem criteria change {task.slug} "
            "--unchanged",
        )
    kept = replace(task.criteria, change=replace(change, pairs=found))
    return waits.asked(replace(task, criteria=kept), change.at, waits.CHANGED, shown)


def unchanged(task: Task, now: datetime, shown: str) -> Task:
    """The task whose same criteria, of file mark `shown`, wait for his yes again after his
    No whose note changes no criterion."""
    question = waits.question_of(task)
    said = question.answer if question else None
    if said is None:
        raise Refusal(
            "no-answer",
            f"no answer of the owner is on record for this wait of {task.slug}'s criteria",
            f"his yes approves them, lem criteria approve {task.slug} --file FILE; his "
            f"typed No is recorded first, lem criteria change {task.slug} --typed "
            '--words "HIS NOTE"',
        )
    if said.option != waits.SAID_NO:
        raise first(said)
    return waits.asked(task, now, waits.UNCHANGED, shown)
