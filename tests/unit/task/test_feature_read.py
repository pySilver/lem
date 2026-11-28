"""A feature's parts as a read, `lem task show` and the session's brief see them
(`docs/plans/2026-11-27-a-feature-in-parts.md`, step 36g): a read keeps the parts in the
feature's `after`, where its landing finds them, and waits for each part that has not ended
whatever `--after` says; `lem task show` gives the parts, and `session.md` has the line
`feature:` for a feature and for a part, so that no session tells a feature by the words of its
ask."""

from typing import TYPE_CHECKING

from fakes.command import lem
from lem.app.sessions import brief
from lem.app.tasks import shape
from lem.model.task.read import Queue
from lem.records.task import Shape
from unit.task.spaces import made, read, result, workspace

if TYPE_CHECKING:
    from pathlib import Path

    from lem.store.places import Workspace

FEATURE = "save-items"
PARTS = ("save-endpoint", "ios-save-button")
LEAD = Shape(type="feat", why="save an item", track="full", then="lead")


def feature(where: Workspace, *statuses: str) -> None:
    """The feature queued after its two parts, each part with its status, and a task it was
    never split into."""
    for slug, status in zip(PARTS, statuses, strict=True):
        made(where, slug, status=status, part_of=FEATURE)
    made(where, "other-task", status="building")
    made(where, FEATURE, status="queued", after=PARTS, shape=LEAD)


def test_a_read_with_no_after_keeps_the_parts_and_lifts_the_queue_once_they_ended(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    feature(where, "landed", "answered")
    shape.shaped(where.checkout, FEATURE, LEAD, Queue())
    task = read(where, FEATURE).task
    assert (task.status, task.after) == ("shaping", PARTS)


def test_a_read_with_no_after_keeps_the_feature_queued_while_a_part_runs(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    feature(where, "landed", "building")
    shape.shaped(where.checkout, FEATURE, LEAD, Queue())
    task = read(where, FEATURE).task
    assert (task.status, task.after) == ("queued", PARTS)


def test_a_read_after_another_task_adds_it_behind_the_parts(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    feature(where, "landed", "landed")
    shape.shaped(where.checkout, FEATURE, LEAD, Queue(after=("other-task",)))
    task = read(where, FEATURE).task
    assert (task.status, task.after) == ("queued", (*PARTS, "other-task"))


def test_a_dropped_part_keeps_the_feature_waiting_for_the_owners_word(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    feature(where, "landed", "dropped")
    shape.shaped(where.checkout, FEATURE, LEAD, Queue())
    task = read(where, FEATURE).task
    assert (task.status, task.after) == ("queued", PARTS)


def test_a_task_with_no_parts_reads_as_before(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, "first", status="landed")
    made(where, "gift-note", status="queued", after=("first",), shape=LEAD)
    shape.shaped(where.checkout, "gift-note", LEAD, Queue())
    task = read(where, "gift-note").task
    assert (task.status, task.after) == ("shaping", ())


def test_task_show_gives_a_features_parts_and_a_parts_feature(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    feature(where, "landed", "building")
    shown = result(lem("task", "show", FEATURE, cwd=tmp_path))
    assert (shown["parts"], shown.get("part_of")) == (list(PARTS), None)
    part = result(lem("task", "show", PARTS[0], cwd=tmp_path))
    assert (part.get("parts", []), part["part_of"]) == ([], FEATURE)
    other = result(lem("task", "show", "other-task", cwd=tmp_path))
    assert other.get("parts", []) == []


def test_the_session_brief_names_the_feature_of_a_feature_and_of_a_part(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    feature(where, "landed", "building")
    lines = {
        slug: brief.feature_line(where.state, read(where, slug).task)
        for slug in (FEATURE, PARTS[1], "other-task")
    }
    assert lines == {
        FEATURE: f"{FEATURE}, in parts: {', '.join(PARTS)}",
        PARTS[1]: f"a part of {FEATURE}",
        "other-task": None,
    }
