"""Release stops on both reads of a landing step."""

from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest
from msgspec.structs import replace

from lem.app.landing import frame, merge, merge_called, step
from lem.app.landing import next as next_step
from lem.kernel import clock
from lem.kernel.errors import Refusal
from lem.records.holds import ReleaseHold
from lem.records.landing.merge import Merged
from lem.store import tasks
from unit.landing.merges import BY_OWNER, DONE, INTENT, facing, opened
from unit.landing.worlds import MOMENT, TREE
from unit.task.spaces import workspace

if TYPE_CHECKING:
    from pathlib import Path

OLD = "0.2.9"


@pytest.mark.parametrize("entry", ["step", "next", "refresh"])
def test_a_landing_entry_or_refresh_refuses_a_task_that_began_two_releases_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, entry: str
) -> None:
    where = workspace(tmp_path)
    live = tasks.create(where.state, opened())
    slug = live.task.slug
    monkeypatch.setattr(frame, "bound", Mock())
    monkeypatch.setattr(frame, "gather", lambda *args, **kwargs: facing())
    monkeypatch.setattr(step, "gather", frame.gather)
    monkeypatch.setattr(next_step, "gather", frame.gather)
    context = step.opened(where, slug, MOMENT)
    tasks.update(
        where.state, slug, lambda before: replace(before, release=OLD), live.revision
    )

    with pytest.raises(Refusal) as refused:
        if entry == "step":
            step.opened(where, slug, MOMENT)
        elif entry == "next":
            next_step.due_now(where.checkout, slug)
        else:
            context.again()
    assert refused.value.code == "release"
    assert isinstance(tasks.read(where.state, slug).task.hold, ReleaseHold)


def test_the_merge_lock_allows_a_forge_result_and_refuses_a_retry_after_the_release_stop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    where = workspace(tmp_path)
    record = tasks.create(where.state, replace(opened(intent=INTENT), release=OLD))
    ports = Mock()
    ports.git.tree.return_value = TREE
    forge_call = Mock()
    monkeypatch.setattr(merge_called, "called", forge_call)
    monkeypatch.setattr(frame, "gather", lambda *args, **kwargs: facing())
    context = frame.Context(ports=ports, workspace=where, record=record, world=facing())
    asked = replace(BY_OWNER, checked=clock.compact(INTENT.at))

    with pytest.raises(Refusal) as refused:
        merge.act(context, asked=asked)
    assert refused.value.code == "release"
    retained = tasks.read(where.state, record.task.slug).landing
    assert retained is not None and retained.intent == INTENT

    monkeypatch.setattr(frame, "gather", lambda *args, **kwargs: facing(pull=DONE))
    assert isinstance(merge.act(context, asked=asked), Merged)
    forge_call.assert_not_called()
