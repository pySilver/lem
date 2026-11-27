"""Which task takes `lem task sync` (`model/task/sync.py`): a feature that waits `queued` on its
branch, and no other; and the subject of the sync's merge commit."""

import pytest

from fakes.records import record
from lem.model.task import sync

FEATURE = "save-items"


def test_a_feature_queued_on_its_branch_takes_a_sync() -> None:
    feature = record(FEATURE, branch="feature/save-items").task
    part = record("save-endpoint", part_of=FEATURE).task
    assert sync.named(FEATURE, (feature, part))
    assert sync.refused(feature, feature=True) is None


@pytest.mark.parametrize(
    ("fields", "feature", "words"),
    [
        pytest.param({}, False, "no task names it", id="no-part"),
        pytest.param({"status": "building"}, True, "is building", id="its-end"),
        pytest.param({"branch": None}, True, "has no branch", id="no-branch"),
    ],
)
def test_a_task_that_is_no_waiting_feature_is_refused(
    fields: dict[str, object], *, feature: bool, words: str
) -> None:
    task = record(FEATURE, **{"branch": "feature/save-items", **fields}).task
    refused = sync.refused(task, feature=feature)
    assert refused is not None
    assert (refused.code, words in refused.why) == ("feature", True)


def test_no_part_names_a_task_of_its_own() -> None:
    alone = record(FEATURE).task
    other = record("other", part_of="another-feature").task
    assert not sync.named(FEATURE, (alone, other))


def test_the_merge_subject_names_the_base_and_the_branch() -> None:
    assert sync.message("main", "feature/x") == "Merge origin/main into feature/x"
