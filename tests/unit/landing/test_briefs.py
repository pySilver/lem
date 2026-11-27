"""The owner's words in the review agent's and the merge agent's briefs: the record's `ask`, the one
place they live, given as text, with the task's files beside them only where the folder has
them (`app/landing/review_brief.py`, `app/landing/merge_facts.py`)."""

from typing import TYPE_CHECKING
from unittest.mock import Mock

import msgspec
from msgspec.structs import replace

from lem.app.landing import frame, merge_facts, review_brief, review_facts
from lem.model.landing import careful
from lem.store import tasks
from unit.landing.merges import facing, opened
from unit.landing.worlds import BASE, PROPOSED, PULL, TIP, task
from unit.task.spaces import workspace

if TYPE_CHECKING:
    from pathlib import Path

ASK = "the login page says recieve; fix the word (docs/backlog/the-word.md)"


def context_of(tmp_path: Path, landing: dict[str, object]) -> frame.Context:
    """A landing's context over a task whose ask is `ASK`, its folder with `task.md` in it,
    and ports that answer every look at git with nothing."""
    where = workspace(tmp_path)
    made = task("open", **landing)
    record = tasks.create(where.state, replace(made, task=replace(made.task, ask=ASK)))
    ports = Mock()
    ports.git.merge_base.return_value = BASE
    ports.git.diff_stat.return_value = Mock(paths=())
    found = frame.Context(ports=ports, workspace=where, record=record, world=facing())
    (found.folder / "task.md").write_text(f"# The task\n\n{ASK}\n")
    return found


def test_the_review_agent_gets_the_owners_words_from_the_record(
    tmp_path: Path,
) -> None:
    context = context_of(tmp_path, {})
    gathered = review_facts.Gathered(
        lines=1, edits=careful.Edits(), at_base=frozenset()
    )
    given = review_brief.inputs(context, gathered, ())
    shown = msgspec.json.decode(msgspec.json.encode(given))
    assert shown["ask"] == ASK
    assert shown["request"] == str(context.folder / "task.md")
    assert "words" not in shown


def test_the_merge_agent_gets_the_owners_words_from_the_record(
    tmp_path: Path,
) -> None:
    context = context_of(tmp_path, {"reads": ()})
    landing = opened().landing
    assert landing is not None
    facts = merge_facts.facts_of(context, landing, (PULL, PROPOSED))
    shown = msgspec.json.decode(msgspec.json.encode(facts))
    assert (shown["task"], shown["ask"], shown["tip"]) == (
        context.record.task.slug,
        ASK,
        TIP,
    )
    assert shown["files"] == {"request": str(context.folder / "task.md")}
