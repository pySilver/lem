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
