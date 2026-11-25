"""Which question an answer of the board is for, and whether its option may stand
(`serve.act_answer` and `row_refusal` on `main`).

The page names the question by its id. The answer is for the question the task's wait asks now,
unanswered; one answered already says which answer took effect, and one whose wait ended or began
again says what holds now. The option is one of the question's; Help and the criteria's No need
the owner's words, and Park and Drop their confirm.
"""

from typing import TYPE_CHECKING

from lem.board.acts import asking, effect
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from lem.board.acts.given import Given
    from lem.records.questions import Question
    from lem.records.task import Task

NOTHING = effect.NOTHING
CONFIRM = "yes"


def question_of(task: Task, key: str) -> Question:
    """The question the answer `key` is for; refused when it waits no more."""
    standing = asking.standing(task)
    if standing is not None and standing.id == key:
        if standing.answer is not None:
            raise effect.answered(standing, standing.answer)
        return standing
    found = next((one for one in task.questions if one.id == key), None)
    if found is not None and found.answer is not None:
        raise effect.answered(found, found.answer)
    topic = key.split(":", 1)[0]
    if found is not None:
        topic = found.topic
    raise effect.gone(task, standing, topic)


def option_of(question: Question, given: Given) -> str:
    """The option of the answer; refused when there is none, or one the question has not."""
    option = given.option
    if not option:
        raise Refusal("option", f"Pick an option first. {NOTHING}", "pick one")
    if option not in question.options:
        labels = ", ".join(asking.label_of(one) for one in question.options)
        why = f"“{question.question}” takes {labels}. {NOTHING}"
        raise Refusal("option", why, "pick one of them")
    return option


def note_refusal(question: Question, option: str, given: Given) -> Refusal | None:
    """Why the option needs more than it got: words for Help and the criteria's No, the
    confirm for Park and Drop."""
    if option == "help" and not given.note:
        why = f"Help needs your words for the lead. {NOTHING}"
        return Refusal("words", why, "write what the lead should hear")
    if question.topic == "criterion" and option == "no" and not given.note:
        why = f"No needs your words: what the criteria should say. {NOTHING}"
        return Refusal("words", why, "write what should change")
    if option in {"park", "drop"} and given.confirm != CONFIRM:
        label = asking.label_of(option)
        why = f"{label} asks for a confirm first. {NOTHING}"
        return Refusal("confirm", why, f"open {label}… and confirm there")
    return None


def checked(question: Question, given: Given) -> str:
    """The option of the answer, once it may stand."""
    option = option_of(question, given)
    refusal = note_refusal(question, option, given)
    if refusal is not None:
        raise refusal
    return option
