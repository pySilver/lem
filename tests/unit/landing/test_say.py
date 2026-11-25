"""What a landing step says comes next: each due step's command is a line the tree takes, with
the caller's inputs as placeholders its `why` names (`app/landing/say.py`)."""

from typing import get_args

import pytest

from lem.app.landing import say
from lem.model.landing.world import Due, Verb
from unit.cli import parsing, reading, shapes

TREE = shapes.tree()
VERBS: tuple[Verb, ...] = get_args(Verb.__value__)


@pytest.mark.parametrize("verb", VERBS)
def test_each_due_steps_command_is_a_line_the_tree_takes(verb: Verb) -> None:
    by = "merger" if verb == "merge" else None
    following = say.following("fix-the-login", Due(step=verb, why="due", by=by))
    assert following.act == "run"
    assert following.command is not None
    line = reading.Line("next", 1, following.command, span=False)
    assert reading.verdict(line, TREE) == []
    assert parsing.clicks_word(line) is None
    if any(word.isupper() for word in following.command.split()):
        assert say.INPUTS in (following.why or "")


def test_the_owners_merge_and_a_rest_are_waits_and_the_end_is_done() -> None:
    owner = say.following("x", Due(step="merge", why="careful", by="owner"))
    assert (owner.act, owner.command) == ("wait", None)
    assert say.following("x", Due(step="wait", why="w")).act == "wait"
    assert say.following("x", Due(step="done", why="d")).act == "done"
