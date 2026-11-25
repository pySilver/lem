"""The reviewer's item leaves with the merge, with a retry if the file cannot be removed."""

from dataclasses import replace as replace_dataclass
from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from fakes.forge import LocalForge
from fakes.git import ModelGit
from fakes.ports import fake_ports
from lem.app.landing import merged
from lem.app.landing.frame import Context
from lem.kernel.errors import Refusal
from lem.store import tasks
from unit.landing.worlds import MERGED, OPENED, PULL, task, world
from unit.task.spaces import workspace

if TYPE_CHECKING:
    from pathlib import Path

ITEM = ".lem/state/backlog/lessons.md"


def ready(checkout: Path) -> Context:
    where = workspace(checkout)
    made = task(
        "open",
        **{**OPENED, "phase": "merged", "merged": replace(MERGED, text_updated=True)},
    )
    record = tasks.create(
        where.state, replace(made, task=replace(made.task, backlog_item=ITEM))
    )
    git = ModelGit(checkout=checkout)
    return Context(
        ports=fake_ports(git, LocalForge(remote=git)),
        workspace=where,
        record=record,
        world=world(),
    )


@pytest.mark.parametrize("present", [True, False])
def test_merge_removes_the_tasks_item_and_accepts_one_gone_already(
    tmp_path: Path, *, present: bool
) -> None:
    context = ready(tmp_path)
    item = tmp_path / ITEM
    if present:
        item.parent.mkdir()
        item.write_text("# Lessons\n")
    merged.act(context)
    assert not item.exists()
    assert (
        tasks.read(context.workspace.state, context.record.task.slug).task.status
        == "landed"
    )


def test_a_failed_item_removal_keeps_the_task_open_and_merged_retries(
    tmp_path: Path,
) -> None:
    context = ready(tmp_path)
    state, slug = context.workspace.state, context.record.task.slug
    item = tmp_path / ITEM
    item.mkdir(parents=True)
    with pytest.raises(Refusal) as caught:
        merged.act(context)
    assert str(item) in caught.value.why
    assert PULL.url in caught.value.why
    assert f"lem land merged {slug}" in caught.value.fix
    record = tasks.read(state, slug)
    assert record.task.status == "open"
    item.rmdir()
    item.write_text("# Lessons\n")
    merged.act(replace_dataclass(context, record=record))
    assert not item.exists()
    assert tasks.read(state, slug).task.status == "landed"
