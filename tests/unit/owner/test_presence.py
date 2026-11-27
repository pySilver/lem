"""The owner's presence, the machine's one mark: where it is, how it reads, and his away and
back through `lem owner` (`main`: `tests/unit/test_owner.py::Mark`, `tests/lem-state.sh` "the
owner's status is one mark of the machine" and "the owner says whether he is there")."""

import os
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import UTC, date, datetime
from pathlib import Path
from threading import Barrier
from typing import TYPE_CHECKING

import msgspec
import pytest

from fakes.command import lem
from lem.app.owner import presence
from lem.kernel import folders, locks, paths
from lem.kernel.errors import Fault, Refusal
from lem.model.owner.spans import spans
from lem.records.owner import Presence
from lem.records.tickets import Ticket
from lem.store import owner, tasks
from unit.task.spaces import made, refusal, result, workspace

if TYPE_CHECKING:
    from collections.abc import Iterator

AWAY_AT = datetime(2026, 11, 19, 14, 5, tzinfo=UTC)
BACK_AT = datetime(2026, 11, 19, 16, 30, tzinfo=UTC)


def home() -> Path:
    return paths.home(os.environ)


def test_the_place_follows_the_variable(tmp_path: Path) -> None:
    assert paths.home({"XDG_CONFIG_HOME": str(tmp_path)}) == tmp_path / "lem"


def test_an_empty_variable_is_the_home_directory() -> None:
    found = paths.home({"XDG_CONFIG_HOME": "", "HOME": "/Users/someone"})
    assert found == Path("/Users/someone/.config/lem")


def test_a_relative_variable_is_refused() -> None:
    with pytest.raises(Refusal) as caught:
        paths.home({"XDG_CONFIG_HOME": "config"})
    assert caught.value.code == "config-home"
    assert "'config', a relative path" in caught.value.why


def test_no_mark_is_the_owner_there_and_makes_nothing() -> None:
    assert owner.read(home()) == Presence()
    assert not home().exists()


def test_the_newest_change_holds() -> None:
    owner.change(home(), "/lem im-away", AWAY_AT, away=True)
    back = owner.change(home(), "/lem im-back", BACK_AT, away=False)
    assert (back.away, back.since, back.words, back.seen) == (
        False,
        BACK_AT,
        "/lem im-back",
        2,
    )
    assert owner.read(home()) == back


def test_his_words_may_hold_a_line_separator() -> None:
    words = "away\u2028now\u2029and\x85later"
    owner.change(home(), words, AWAY_AT, away=True)
    assert owner.read(home()).words == words


def test_a_mark_that_does_not_read_is_a_fault_with_its_place() -> None:
    home().mkdir(parents=True)
    (home() / "owner.json").write_text("not json\n", encoding="utf-8")
    with pytest.raises(Fault) as caught:
        owner.read(home())
    assert str(home() / "owner.json") in str(caught.value)


def test_away_names_every_open_task_and_writes_once(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, "report-dates", status="building")
    made(where, "old-task", status="landed")
    first = lem("owner", "away", "--words", "I'm away", cwd=tmp_path)
    assert result(first) | {"since": None} == {
        "away": True,
        "since": None,
        "words": "I'm away",
        "written": True,
        "tasks": ["report-dates"],
        "seen": 1,
    }
    result(lem("task", "open", "new-task", "--ask", "sort the dates", cwd=tmp_path))
    opened = tasks.read(where.state, "new-task").task
    (running,) = spans(opened, owner.read(home()))
    assert (running.start, running.end) == (opened.opened, None)
    again = result(lem("owner", "away", "--words", "away again", cwd=tmp_path))
    assert (again["written"], again["words"], again["tasks"]) == (
        False,
        "I'm away",
        ["new-task", "report-dates"],
    )
    assert not (where.state / "tasks" / "report-dates" / "owner.json").exists()
    assert owner.read(home()).seen == 1
    back = result(lem("owner", "back", "--words", "I'm back", cwd=tmp_path))
    assert back["tasks"] == ["new-task", "report-dates"]
    (closed,) = spans(opened, owner.read(home()))
    assert (closed.start, closed.end) == (opened.opened, owner.read(home()).since)


@pytest.mark.parametrize("second_words", ["I'm away", "Away at lunch"])
def test_simultaneous_aways_write_once_across_repositories(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, second_words: str
) -> None:
    first = workspace(tmp_path / "first")
    second = workspace(tmp_path / "second")
    folders.home_marked(home())
    both = Barrier(2, timeout=5)
    held = locks.held

    @contextmanager
    def together(path: Path) -> Iterator[None]:
        if path == home() / owner.LOCK:
            both.wait()
        with held(path):
            yield

    monkeypatch.setattr(locks, "held", together)
    with ThreadPoolExecutor(max_workers=2) as pool:
        one = pool.submit(presence.said, first.checkout, "I'm away", AWAY_AT, away=True)
        two = pool.submit(
            presence.said, second.checkout, second_words, AWAY_AT, away=True
        )
        found = (one.result(), two.result())

    mark = owner.read(home())
    assert sorted(said.written for said in found) == [False, True]
    assert mark.seen == len(mark.changes) == 1
    assert {said.seen for said in found} == {1}
    assert {said.words for said in found} == {mark.words}


def test_broken_settings_with_a_ticket_refuse_away_before_the_mark(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path, settings="[branch")
    made(where, "report-dates", ticket=Ticket(tracker="linear", id="DEMO-12"))
    before = owner.read(home())
    stopped = refusal(lem("owner", "away", "--words", "I'm away", cwd=tmp_path))
    assert stopped["code"] == "settings-toml"
    assert owner.read(home()) == before


def test_back_takes_back_every_task_but_a_nights(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, "report-dates", status="building")
    made(where, "night-item", status="building", night=date(2026, 11, 19), mode="alone")
    lem("owner", "away", "--words", "I'm away", cwd=tmp_path)
    back = result(lem("owner", "back", "--words", "/lem im-back", cwd=tmp_path))
    assert (back["away"], back["written"], back["tasks"]) == (
        False,
        True,
        ["report-dates"],
    )
    again = result(lem("owner", "back", "--words", "/lem im-back", cwd=tmp_path))
    assert (again["written"], again["tasks"], again["seen"]) == (False, [], 2)


def test_his_away_in_one_repository_is_read_in_another(tmp_path: Path) -> None:
    workspace(tmp_path / "first")
    workspace(tmp_path / "second")
    said = result(lem("owner", "away", "--words", "I'm away", cwd=tmp_path / "first"))
    listed = result(lem("waiting", cwd=tmp_path / "second"))
    assert listed["owner"] == {
        "away": True,
        "since": said["since"],
        "words": "I'm away",
        "seen": 1,
    }


@pytest.mark.parametrize("command", ["away", "back"])
def test_a_broken_task_record_leaves_the_machine_mark_as_it_was(
    tmp_path: Path, command: str
) -> None:
    where = workspace(tmp_path)
    made(where, "report-dates", status="building")
    task_record = where.state / "tasks" / "report-dates" / "task.json"
    task_record.write_text("not json", encoding="utf-8")
    if command == "back":
        owner.change(home(), "away", AWAY_AT, away=True)
    before = owner.read(home())
    found = lem("owner", command, "--words", command, cwd=tmp_path)
    refused = refusal(found)
    assert refused["code"] == "unread-task-record"
    assert str(task_record) in refused["why"]
    assert owner.read(home()) == before


def test_a_word_with_no_words_is_refused(tmp_path: Path) -> None:
    workspace(tmp_path)
    assert refusal(lem("owner", "away", cwd=tmp_path))["code"] == "words"
    assert (
        refusal(lem("owner", "back", "--words", "  ", cwd=tmp_path))["code"] == "words"
    )
    # the command put the repository on the machine's list first (`cli/listing.py`); its
    # refusal wrote no presence
    assert not (home() / "owner.json").exists()


def test_the_mark_is_one_json_record_of_each_change() -> None:
    owner.change(home(), "away", AWAY_AT, away=True)
    owner.change(home(), "back", BACK_AT, away=False)
    raw = msgspec.json.decode((home() / "owner.json").read_bytes())
    assert [(one["away"], one["words"]) for one in raw["changes"]] == [
        (True, "away"),
        (False, "back"),
    ]
