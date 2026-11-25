"""The texts an agent of a task follows at its interview, plan, build, plan talk, ladder and
breaker are carried in the plugin's files, and each `lem` line in them is one the tree takes.
The one line left of the old form, in the breaker's stage, asks the breaker's row of the board
again, which no command of the tree does yet (`notes/criteria.md`)."""

from types import MappingProxyType

import pytest

from lem.kernel import paths
from unit.cli import reading, shapes

TEXTS = (
    "skills/lem/stages/interview.md",
    "skills/lem/stages/plan.md",
    "skills/lem/stages/build.md",
    "skills/lem/stages/talk.md",
    "skills/lem/stages/ladder.md",
    "skills/lem/stages/breaker.md",
    "skills/lem/prompts/lead.md",
    "skills/lem/prompts/defender.md",
    "skills/lem/prompts/reviewer.md",
    "skills/lem/prompts/writing.md",
    "skills/lem/templates/handoff.md",
    "skills/lem/templates/breaker.md",
    "agents/lem-builder.md",
    "skills/lem-gate/SKILL.md",
    "skills/lem-interview-me/SKILL.md",
    "skills/lem-dialectic/SKILL.md",
    "skills/lem-root-cause/SKILL.md",
)
# The old lines a text keeps, by the text.
ASKED_AGAIN = 'lem project state SLUG held "breaker N waits for the owner" "YOUR ONE LINE TO HIS NOTE"'
KEPT = MappingProxyType({"skills/lem/stages/breaker.md": (ASKED_AGAIN,)})
TREE = shapes.tree()


@pytest.mark.parametrize("name", TEXTS)
def test_each_text_of_the_step_is_carried_in_the_new_form(name: str) -> None:
    path = paths.root() / name
    text = path.read_text(encoding="utf-8")
    old = [
        line.text
        for line in reading.lines_of(text, name)
        if reading.verdict(line, TREE)
    ]
    assert old == list(KEPT.get(name, ()))
    assert reading.marked(text) == bool(old)
    assert text.count("lem project") == len(old)


# Each ruling of the owner that one of the step's texts carries, by the ruling's id, with the
# text and the words of it that hold the ruling.
RULINGS = (
    (
        "a-full-change-has-one-approval",
        "skills/lem/stages/interview.md",
        "he says yes once",
    ),
    (
        "a-plan-may-end-with-a-documentation-task",
        "skills/lem/stages/plan.md",
        "documentation task, last, when the change makes a document false",
    ),
    (
        "each-task-of-a-plan-gets-a-fresh-builder",
        "skills/lem/stages/build.md",
        "Each task of the plan gets a fresh builder",
    ),
    (
        "every-project-of-lem-has-personas",
        "skills/lem/stages/interview.md",
        'persona panel\'s "Reading acceptance criteria" mode',
    ),
    (
        "lem-brings-its-own-builder-agent",
        "agents/lem-builder.md",
        "model: opus effort: high",
    ),
    (
        "most-requests-have-an-interview",
        "skills/lem/stages/interview.md",
        "One question at a time, each with your own guess",
    ),
    (
        "the-build-asks-him-nothing",
        "skills/lem/stages/ladder.md",
        "nothing of a build waits for him",
    ),
    (
        "the-personas-read-first",
        "skills/lem/stages/interview.md",
        "Show them in the conversation, and start the personas' read in the same moment",
    ),
    (
        "the-plan-talk-is-a-pair",
        "skills/lem/stages/talk.md",
        "Companion is closed once discussion is done",
    ),
    (
        "the-plan-talk-is-predictably-short",
        "skills/lem/stages/talk.md",
        "The list closes with the reviewer's first turn.",
    ),
    (
        "the-question-gate-stays-hidden",
        "skills/lem-gate/SKILL.md",
        "it should stay as hidden feature",
    ),
    (
        "the-session-s-answers-to-his-notes",
        "skills/lem/stages/plan.md",
        "this task builds on what another task changes",
    ),
    (
        "two-builders-of-one-plan",
        "agents/lem-builder.md",
        "Never stage a path that is not your task's",
    ),
    (
        "when-the-personas-flag-a-criterion",
        "skills/lem/stages/interview.md",
        "as a rewrite of the personas' that keeps its rule is taken",
    ),
)


@pytest.mark.parametrize(
    ("ruling", "name", "words"), RULINGS, ids=[one[0] for one in RULINGS]
)
def test_each_ruling_the_step_carries_is_in_its_text(
    ruling: str, name: str, words: str
) -> None:
    text = " ".join((paths.root() / name).read_text(encoding="utf-8").split())
    assert words in text, ruling
