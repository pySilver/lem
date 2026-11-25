"""The reviewer's item leaves with the merge, with a retry if the file cannot be removed."""

from dataclasses import replace as replace_dataclass
from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from fakes.forge import LocalForge
from fakes.git import ModelGit
from fakes.ports import fake_ports
from lem.addons.proposals import listing
from lem.addons.proposals.listed import PassedOne
from lem.app.landing import merged
from lem.app.landing.frame import Context
from lem.kernel.errors import Refusal
from lem.store import tasks
from unit.addons.flow.runs import add, judge, proposal
from unit.landing.worlds import MERGED, OPENED, PULL, task, world
from unit.task.spaces import workspace

if TYPE_CHECKING:
    from pathlib import Path

ITEM = ".lem/state/backlog/lessons.md"


def ready(checkout: Path, backlog_item: str = ITEM) -> Context:
    where = workspace(checkout)
    made = task(
        "open",
        **{**OPENED, "phase": "merged", "merged": replace(MERGED, text_updated=True)},
    )
    record = tasks.create(
        where.state, replace(made, task=replace(made.task, backlog_item=backlog_item))
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


def test_merge_removes_an_item_claimed_under_a_path_alias(tmp_path: Path) -> None:
    context = ready(tmp_path, ".lem/state/backlog/../backlog/lessons.md")
    item = tmp_path / ITEM
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


def test_a_merge_retry_leaves_the_item_of_a_later_verdict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    context = ready(tmp_path)
    state, slug = context.workspace.state, context.record.task.slug
    old = tmp_path / ITEM
    old.parent.mkdir()
    old.write_text("# Lessons\n")

    def cut_off(_context: Context) -> None:
        raise InterruptedError

    with monkeypatch.context() as patch:
        patch.setattr(merged, "followed", cut_off)
        with pytest.raises(InterruptedError):
            merged.act(context)
    assert not old.exists()
    record = tasks.read(state, slug)
    assert record.task.status == "open"

    added = add(state, "retro", [proposal("lessons", "A new lesson")])
    verdict = {"proposal": added.names[0], "passed": "lessons"}
    made = judge(state, [verdict], {"lessons": "Lessons"}).items_made[0]
    new = tmp_path / made.path
    before = new.read_bytes()
    merged.act(replace_dataclass(context, record=record))
    assert new.is_file()
    assert new.read_bytes() == before
    assert new.name == "lessons-2.md"
    assert tasks.read(state, slug).task.status == "landed"

    next_run = add(state, "retro", [proposal("lessons", "A third lesson")])
    verdict = {"proposal": next_run.names[0], "passed": "lessons"}
    made = judge(state, [verdict], {"lessons": "Lessons"}).items_made[0]
    assert made.path == ITEM


def test_a_reused_item_path_does_not_mark_the_landed_proposal_present(
    tmp_path: Path,
) -> None:
    state = workspace(tmp_path).state
    old = add(state, "retro", [proposal("lessons", "An old lesson")]).names[0]
    verdict = {"proposal": old, "passed": "lessons"}
    assert judge(state, [verdict], {"lessons": "Lessons"}).items_made[0].path == ITEM
    merged.act(ready(tmp_path))
    (landed,) = listing.listed(state).passed
    assert isinstance(landed, PassedOne)
    assert not landed.there

    new = add(state, "retro", [proposal("lessons", "A new lesson")]).names[0]
    verdict = {"proposal": new, "passed": "lessons"}
    assert judge(state, [verdict], {"lessons": "Lessons"}).items_made[0].path == ITEM
    assert {
        one.name: one.there
        for one in listing.listed(state).passed
        if isinstance(one, PassedOne)
    } == {
        old: False,
        new: True,
    }
