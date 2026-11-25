"""The answer the board takes to a question of a task (`board_pages.answer_form` and
`board_model.answer_row` on `main`): the question as the record asked it, one note, and one
button for each option; Park and Drop open their confirm step first, with the note typed so far.

The same form stands on a row of Waits for you and on the task's panel; `where` tells the two
apart in the ids, which a refresh keeps while the owner types.
"""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.board.inputs.forms import AnswerForm, Choice, Field, TextBox
from lem.board.inputs.names import task_href

if TYPE_CHECKING:
    from lem.board.inputs.text import Press
    from lem.board.views.world import World
    from lem.records.questions import Question

# What the note asks for, by the question's topic: Help, and No on the criteria, need words.
NOTES = MappingProxyType(
    {
        "plan": "A note for the task’s session, if you like",
        "breaker": "Help needs your words for the lead",
        "skip": "A note for the task’s session, if you like",
        "criterion": "No needs your words: what should the criteria say?",
    }
)
TYPED = "Your words, as you would type them in the session"
# Each option's words, icon and look.
OPTIONS: MappingProxyType[str, tuple[str, str, Press]] = MappingProxyType(
    {
        "build": ("Build", "play", "go"),
        "help": ("Help", "circle-question", "go"),
        "yes": ("Yes", "check", "go"),
        "no": ("No", "xmark", "plain"),
        "park": ("Park", "folder", "plain"),
        "drop": ("Drop", "xmark", "risk"),
    }
)
# The options that ask first, each on a confirm step of its own.
CONFIRMED = frozenset(("park", "drop"))


def form(
    world: World,
    question: Question,
    where: str,
    under: str | None = None,
    tab: str | None = None,
) -> AnswerForm | None:
    """The answer to `question`, on the row or the panel `where`; None where the page may
    not act. `under` is the view under the panel, `tab` the tab it posts back to."""
    if not world.viewer.may_act:
        return None
    slug = question.id.split(":")[1]
    key = question.id.replace(":", "-")
    base, workspace = world.viewer.base, world.viewer.workspace
    return AnswerForm(
        id=f"answer-{where}-{key}",
        action=f"{task_href(base, slug)}/answer",
        question=question.question,
        fields=fields_of(question, under, tab),
        note=TextBox(
            name="words",
            id=f"ans-{where}-{workspace}-{key}",
            label=NOTES.get(question.topic),
            placeholder=TYPED,
            rows=2,
        ),
        choices=tuple(
            choice(base, slug, option)
            for option in question.options
            if option in OPTIONS
        ),
    )


def fields_of(
    question: Question, under: str | None, tab: str | None
) -> tuple[Field, ...]:
    """The hidden fields: the question's id, the digest the page showed, the tab, the view
    under the panel."""
    named = (
        ("key", question.id),
        ("digest", question.digest),
        ("tab", tab),
        ("in", None if under == "tasks" else under),
    )
    kept = ((name, shown) for name, shown in named if shown)
    return tuple(Field(name=name, shown=shown) for name, shown in kept)


def choice(base: str, slug: str, option: str) -> Choice:
    """One option's button; Park and Drop link to their confirm step."""
    label, icon, press = OPTIONS[option]
    if option in CONFIRMED:
        confirm = f"{task_href(base, slug)}/{option}"
        return Choice(
            option=option, label=f"{label}…", icon=icon, press=press, confirm=confirm
        )
    return Choice(option=option, label=label, icon=icon, press=press)
