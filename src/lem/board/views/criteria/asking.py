"""The owner's answer to the criteria's wait on the tab (`board_pages.answer_form` on `main`):
the one answer form of the wait's question, Yes, or No with his words, with the question's id and
the digest of the text it shows; and what his answer on record says until the task's session
takes it."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.board.inputs.clock import stamp
from lem.board.inputs.forms import AnswerForm, Choice, Field, TextBox
from lem.board.inputs.waits import Acts
from lem.model.criteria import digest, waits

if TYPE_CHECKING:
    from lem.board.views.world import Seen, World
    from lem.records.questions import Question
    from lem.records.task import Task

WAITING = "criteria.md"
TYPED = "Your words, as you would type them in the session"
NOTE = "No needs your words: what should the criteria say?"
FAST_NOTE = "No needs your words: what should the criterion say?"
ON_RECORD = "Your answer is on record: the task’s session takes it."
CHOICES = (
    Choice(option="yes", label="Yes", icon="check", press="go"),
    Choice(option="no", label="No", icon="xmark"),
)


def fast(task: Task) -> bool:
    """Whether the criteria are the fast track's one criterion of a request someone else
    wrote."""
    shape = task.shape
    return shape is not None and shape.track == "small" and shape.someone_else


def shown_question(task: Task, text: str | None) -> Question | None:
    """The open question with the digest of the page's read, when its recorded mark agrees."""
    question = waits.question_of(task)
    if text is None or question is None or question.answer is not None:
        return None
    shown = digest.shown(text.encode())
    if question.digest is not None and question.digest != shown:
        return None
    return replace(question, digest=shown)


def form_of(
    world: World, task: Task, question: Question, where: str = "panel"
) -> AnswerForm:
    """The answer form of the wait's question, on the task's panel."""
    key = question.id.replace(":", "-")
    workspace = world.viewer.workspace
    note = TextBox(
        name="words",
        id=f"ans-{where}-{workspace}-{key}",
        label=FAST_NOTE if fast(task) else NOTE,
        placeholder=TYPED,
        rows=2,
    )
    base = world.viewer.base
    return AnswerForm(
        id=f"answer-{where}-{key}",
        action=f"{base}/tasks/{task.slug}/answer",
        question=question.question,
        fields=fields_of(world, question, where),
        note=note,
        choices=CHOICES,
    )


def fields_of(world: World, question: Question, where: str) -> tuple[Field, ...]:
    """The hidden fields: the question's id, the digest of the text it shows, the tab, and
    the view under the panel."""
    fields = [Field(name="key", shown=question.id)]
    if question.digest:
        fields.append(Field(name="digest", shown=question.digest))
    if where == "panel":
        fields.append(Field(name="tab", shown="criteria"))
    if world.viewer.view != "tasks":
        fields.append(Field(name="in", shown=world.viewer.view))
    return tuple(fields)


def inline(world: World, seen: Seen) -> Acts | None:
    """The fast track's criterion and its answer on the row that waits for it."""
    task = seen.record.task
    text = seen.text(WAITING)
    question = shown_question(task, text)
    if question is None:
        return None
    return Acts(criterion=text, answer=form_of(world, task, question, where="row"))


def took_of(world: World, question: Question) -> str | None:
    """What the owner's answer on record says, or None with no answer."""
    answer = question.answer
    if answer is None:
        return None
    where = ""
    if answer.device:
        where = f", from the {answer.device}"
    elif answer.source == "session":
        where = ", in the task’s session"
    when = stamp(answer.at, world.clock.now, world.clock.zone)
    label = answer.label or answer.option
    return f"{ON_RECORD} You picked {label} on “{question.question}” at {when}{where}."
