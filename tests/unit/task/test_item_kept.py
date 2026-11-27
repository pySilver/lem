"""`lem task keep-item`: a task whose request named a backlog item for other work, or whose approved
criteria do not cover the item's whole run, leaves the item in the backlog with the reason; the
own-item gate then asks no removal of it (`model/task/item_kept.py`)."""

from typing import TYPE_CHECKING

import pytest

from fakes.command import lem
from fakes.records import MOMENT, record
from lem.kernel.errors import Refusal
from lem.model.landing.propose_facts import Facts
from lem.model.landing.propose_gates import own_item
from lem.model.task import item_kept
from lem.records.journal.task import StateNoted
from unit.task.spaces import made, read, refusal, result, workspace

if TYPE_CHECKING:
    from pathlib import Path

SLUG = "dates"
ITEM = "docs/backlog/date.md"


def test_the_item_stays_with_its_reason_and_the_gate_asks_no_removal() -> None:
    held = record(SLUG, status="building", backlog_item=ITEM)
    in_tip = Facts(notes="none\n", in_tip=frozenset((ITEM,)))
    assert own_item(held, in_tip) is not None
    kept = item_kept.kept(held, why="the end date is a later task", now=MOMENT)
    assert kept.task.backlog_item is None
    last = kept.journal[-1]
    assert isinstance(last, StateNoted)
    assert (
        last.line
        == f"the item {ITEM} stays in the backlog: the end date is a later task"
    )
    assert own_item(kept, in_tip) is None


@pytest.mark.parametrize(
    ("fields", "why", "code"),
    [
        ({"status": "building"}, "w", "no-item"),
        ({"status": "landed", "backlog_item": ITEM}, "w", "task-ended"),
        ({"status": "building", "backlog_item": ITEM}, "  ", "why"),
    ],
    ids=["no-item", "ended", "no-why"],
)
def test_a_task_with_no_item_an_ended_one_and_no_reason_are_refused(
    fields: dict[str, object], why: str, code: str
) -> None:
    with pytest.raises(Refusal) as refused:
        item_kept.kept(record(SLUG, **fields), why=why, now=MOMENT)
    assert refused.value.code == code


def test_the_command_leaves_the_item_and_show_names_it_no_more(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="building", backlog_item=ITEM)
    ran = lem("task", "keep-item", SLUG, "--why", "the start date only", cwd=tmp_path)
    assert result(ran) == {"slug": SLUG, "stays": ITEM}
    assert read(where, SLUG).task.backlog_item is None
    assert "backlog_item" not in result(lem("task", "show", SLUG, cwd=tmp_path))
    again = lem("task", "keep-item", SLUG, "--why", "again", cwd=tmp_path)
    assert refusal(again)["code"] == "no-item"
