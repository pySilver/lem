"""A task's record: created once, read whole, updated under the record lock with the revision
the writer read, and never torn by a cut-off between the temporary file and the rename."""

import threading
from pathlib import Path

import msgspec
import pytest

from fakes.records import MOMENT, noted, record
from lem.kernel import release
from lem.kernel.errors import Fault, Refusal
from lem.records.journal.task import StateNoted
from lem.records.landing.record import Landing
from lem.records.record import Record
from lem.store import guard, places, tasks


def test_a_created_task_reads_back_at_revision_one(tmp_path: Path) -> None:
    made = tasks.create(tmp_path, record())
    assert made.revision == 1
    assert tasks.read(tmp_path, "fix-the-login") == made
    written = (tmp_path / "tasks" / "fix-the-login" / "task.json").read_text()
    assert written.startswith(
        f'{{\n  "schema": 1,\n  "release": "{release.running()}",\n  "revision": 1,'
    )
    assert written.endswith("}\n")


def test_a_task_is_created_once(tmp_path: Path) -> None:
    tasks.create(tmp_path, record())
    with pytest.raises(Refusal) as refused:
        tasks.create(tmp_path, record())
    assert refused.value.code == "task-exists"


def test_a_missing_task_is_refused_and_a_damaged_record_is_a_fault(
    tmp_path: Path,
) -> None:
    with pytest.raises(Refusal) as refused:
        tasks.read(tmp_path, "fix-the-login")
    assert refused.value.code == "no-task"
    guard.writable(tmp_path)
    folder = tmp_path / "tasks" / "fix-the-login"
    folder.mkdir(parents=True)
    (folder / "task.json").write_text("{")
    with pytest.raises(Fault, match="is no task record"):
        tasks.read(tmp_path, "fix-the-login")


def test_a_slug_that_is_no_folder_name_is_refused(tmp_path: Path) -> None:
    for slug in ("../escape", "Upper", "a/b", "", "-lead", "trail-"):
        with pytest.raises(Refusal) as refused:
            places.task_folder(tmp_path, slug)
        assert refused.value.code == "slug"


def test_an_update_writes_the_next_revision_and_a_stale_one_is_refused(
    tmp_path: Path,
) -> None:
    tasks.create(tmp_path, record())
    after = tasks.update(tmp_path, "fix-the-login", noted("first"), expect=1)
    assert after.revision == 2
    assert len(after.journal) == 1
    with pytest.raises(Refusal) as refused:
        tasks.update(tmp_path, "fix-the-login", noted("second"), expect=1)
    assert refused.value.code == "stale"
    assert "revision 2, not 1" in refused.value.why
    assert tasks.read(tmp_path, "fix-the-login") == after


def test_writers_that_retry_on_a_stale_revision_lose_no_write(tmp_path: Path) -> None:
    tasks.create(tmp_path, record())
    writers, writes = 8, 10

    def write_all(name: str) -> None:
        for number in range(writes):
            while True:
                seen = tasks.read(tmp_path, "fix-the-login").revision
                try:
                    tasks.update(
                        tmp_path, "fix-the-login", noted(f"{name}-{number}"), seen
                    )
                except Refusal:
                    continue
                break

    threads = [
        threading.Thread(target=write_all, args=(f"w{n}",)) for n in range(writers)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    last = tasks.read(tmp_path, "fix-the-login")
    assert last.revision == 1 + writers * writes
    lines = {entry.line for entry in last.journal if isinstance(entry, StateNoted)}
    assert len(lines) == writers * writes


def test_a_cut_off_before_the_rename_leaves_the_record_before_and_no_temporary_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    before = tasks.create(tmp_path, record())

    def cut_off(self: Path, target: Path) -> Path:
        raise OSError("the power went")

    monkeypatch.setattr(Path, "replace", cut_off)
    with pytest.raises(OSError, match="the power went"):
        tasks.update(tmp_path, "fix-the-login", noted("lost"), expect=1)
    monkeypatch.undo()
    folder = tmp_path / "tasks" / "fix-the-login"
    assert tasks.read(tmp_path, "fix-the-login") == before
    assert sorted(path.name for path in folder.iterdir()) == ["task.json", "task.lock"]


def test_a_temporary_file_a_killed_writer_left_is_never_read_as_a_task(
    tmp_path: Path,
) -> None:
    tasks.create(tmp_path, record())
    folder = tmp_path / "tasks" / "fix-the-login"
    (folder / ".task.json.k1ll3d").write_text('{"half": ')
    assert [found.task.slug for found in tasks.every(tmp_path)] == ["fix-the-login"]


def test_every_task_is_read_by_slug(tmp_path: Path) -> None:
    assert tasks.every(tmp_path) == ()
    for slug in ("b-task", "a-task"):
        tasks.create(tmp_path, record(slug))
    assert [found.task.slug for found in tasks.every(tmp_path)] == ["a-task", "b-task"]


def test_a_record_of_a_newer_release_with_a_key_beside_the_old_ones_still_reads(
    tmp_path: Path,
) -> None:
    newer = msgspec.json.encode(record())
    widened = newer.replace(b'"ask":', b'"asked_by":"a teammate","ask":', 1)
    read = msgspec.json.decode(widened, type=Record)
    assert read.task.ask == "fix the login"
    assert read.task.opened == MOMENT


def test_the_state_folder_hides_itself_from_git(tmp_path: Path) -> None:
    state = places.state_of(tmp_path)
    assert state == tmp_path / ".lem" / "state"
    assert (state / ".gitignore").read_text() == "*\n"
    assert places.state_of(tmp_path) == state


def test_a_record_of_a_newer_form_or_release_reads_but_is_never_written_over(
    tmp_path: Path,
) -> None:
    tasks.create(tmp_path, record())
    path = tmp_path / "tasks" / "fix-the-login" / "task.json"
    kept = path.read_text()
    newer_form = kept.replace('"schema": 1,', '"schema": 2,').replace(
        '"ask":', '"asked_by": "a teammate",\n    "ask":'
    )
    for body, code in (
        (newer_form, "record-form"),
        (
            kept.replace(f'"release": "{release.running()}"', '"release": "9.0.0"'),
            "newer-release",
        ),
    ):
        path.write_text(body)
        assert tasks.read(tmp_path, "fix-the-login").task.ask == "fix the login"
        with pytest.raises(Refusal) as refused:
            tasks.update(tmp_path, "fix-the-login", noted("lost"), expect=1)
        assert refused.value.code == code
        assert path.read_text() == body


def test_a_record_that_would_not_read_back_is_never_written(tmp_path: Path) -> None:
    tasks.create(tmp_path, record())

    def abbreviated(before: Record) -> Record:
        return msgspec.structs.replace(before, landing=Landing(pushed="abc1234"))

    with pytest.raises(Fault, match=r"\$\.landing\.pushed"):
        tasks.update(tmp_path, "fix-the-login", abbreviated, expect=1)
    bad_moment = msgspec.structs.replace(
        record("other"),
        task=msgspec.structs.replace(
            record("other").task, opened=MOMENT.replace(tzinfo=None)
        ),
    )
    with pytest.raises(Fault, match="would not read back"):
        tasks.create(tmp_path, bad_moment)
    assert [found.task.slug for found in tasks.every(tmp_path)] == ["fix-the-login"]


def test_a_record_keeps_every_character_as_itself(tmp_path: Path) -> None:
    tasks.create(tmp_path, record(ask="fix the café’s login – ✓"))
    written = (tmp_path / "tasks" / "fix-the-login" / "task.json").read_text()
    assert '"ask": "fix the café’s login – ✓"' in written
