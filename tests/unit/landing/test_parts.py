"""The parts a feature's landing reads (`app/tasks/parts.py`): only the tasks its `after`
names, each that names it in `part_of`, whatever its status; nothing more for a task whose
`after` is empty, and nothing for a part."""

from typing import TYPE_CHECKING

from fakes.records import record
from lem.app.tasks import parts
from lem.store import places, task_file, tasks

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def state_of(folder: Path) -> Path:
    """A workspace's state folder in `folder`."""
    (folder / ".git").mkdir(parents=True)
    (folder / ".lem").mkdir()
    return places.state_of(folder)


def test_a_feature_reads_the_parts_its_after_names_whatever_their_status(
    tmp_path: Path,
) -> None:
    state = state_of(tmp_path)
    tasks.create(state, record("landed-part", part_of="x", status="landed"))
    tasks.create(state, record("dropped-part", part_of="x", status="dropped"))
    tasks.create(state, record("waited-for", status="landed"))
    tasks.create(state, record("unnamed-part", part_of="x", status="building"))
    named = ("landed-part", "dropped-part", "waited-for", "gone")
    feature = record("x", status="building", after=named).task
    found, unread = parts.of(state, feature)
    assert [one.task.slug for one in found] == ["landed-part", "dropped-part"]
    assert unread == ()
    assert parts.named(state, feature)


def test_a_record_that_does_not_read_is_kept_once_a_part_names_the_task(
    tmp_path: Path,
) -> None:
    state = state_of(tmp_path)
    tasks.create(state, record("a-part", part_of="x", status="landed"))
    tasks.create(state, record("broken", status="landed"))
    (places.task_folder(state, "broken") / task_file.RECORD).write_text("{")
    feature = record("x", after=("a-part", "broken")).task
    assert parts.of(state, feature)[1] == ("broken",)


def test_a_task_with_no_after_and_a_part_read_no_other_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = state_of(tmp_path)
    tasks.create(state, record("a-part", part_of="x", status="landed"))
    read: list[Path] = []
    real = task_file.read

    def counted(path: Path) -> object:
        read.append(path)
        return real(path)

    monkeypatch.setattr(task_file, "read", counted)
    assert parts.of(state, record("plain").task) == ((), ())
    assert parts.of(state, record("a-part", part_of="x", after=("x",)).task) == ((), ())
    assert read == []
