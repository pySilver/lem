"""`lem picker`: its rows, their words and their order, and the way to the task picked (`main`:
tests/lem-picker.sh and tests/unit/test_picker.py, `picker.py`). agterm is the fake terminal of
the ports, and the board's opening a stand-in that records what it was asked."""

import datetime as dt
import json
from dataclasses import replace as replace_dataclass
from subprocess import CompletedProcess
from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from fakes.command import lem
from fakes.forge import LocalForge
from fakes.git import ModelGit
from fakes.ports import fake_ports
from fakes.records import MOMENT, record
from fakes.terminal import FakeTerminal
from lem.adapters import terminal_agterm
from lem.addons.picker import board, looks, picking, row, rows, sessions, words
from lem.app.sessions.here import Here
from lem.kernel.errors import Refusal
from lem.model.owner import waiting
from lem.ports.faults import Unanswered
from lem.ports.terminal import PickRow
from lem.records.holds import BreakerHold, OwnerHold, Parked
from lem.records.landing.record import Landing, Pull
from lem.records.task import Shape
from unit.owner.looked import look, proposed
from unit.task.spaces import made, refusal, workspace
from unit.task.spaces import rows as printed

if TYPE_CHECKING:
    from pathlib import Path

    from lem.model.owner.looks import Look

NOW = MOMENT + dt.timedelta(hours=3)


def picked_rows(found: list[Look]) -> tuple[PickRow, ...]:
    records = looks.records_of(tuple(found))
    waits = waiting.rows(tuple(found), away=False, now=NOW)
    return rows.rows_of(records, waits, NOW)


def at(hours: float) -> dt.datetime:
    return MOMENT - dt.timedelta(hours=hours)


def test_each_row_is_the_ask_with_the_state_track_age_and_pull_request(
    tmp_path: Path,
) -> None:
    pull = Pull(number=44, url="https://github.com/o/r/pull/44", title="Gift note")
    landing = Landing(phase="open", pull=pull, proposed=proposed(green=False))
    shape = Shape(type="feat", why="a new note", track="small")
    found = [
        replace(
            look(
                "gift-note",
                ask="add a gift\nnote\tto orders",
                status="open",
                shape=shape,
            ),
            record=replace(
                record(
                    "gift-note",
                    ask="add a gift\nnote\tto orders",
                    status="open",
                    shape=shape,
                ),
                landing=landing,
            ),
        )
    ]
    picked = picked_rows(found)
    assert [(one.row_id, one.label, one.subtitle) for one in picked] == [
        (
            "gift-note",
            "add a gift note to orders",
            "Waits for the merge · fast track · 3h · #44 not green",
        ),
        (row.ALL, "All tasks", "the board of every task · 1 task"),
    ]
    assert tmp_path.is_dir()


def test_the_rows_come_in_the_order_a_developer_reads_them() -> None:
    found = [
        look("old-landed", status="landed", since=at(24 * 30)),
        look("queued-one", status="queued", since=at(1)),
        look("builds-one", status="building", since=at(2)),
        look("parked-one", status="building", hold=Parked(since=at(1))),
        look(
            "ask-criteria",
            status="shaping",
            hold=OwnerHold(on="criteria", line="read", since=at(3)),
        ),
        look("breaker-one", status="building", hold=BreakerHold(number=2, since=at(4))),
        look("new-landed", status="landed", since=at(1)),
    ]
    picked = picked_rows(found)
    assert [one.row_id for one in picked] == [
        "breaker-one",
        "ask-criteria",
        "builds-one",
        "queued-one",
        "parked-one",
        "new-landed",
        "old-landed",
        row.ALL,
    ]
    said = {one.row_id: one.subtitle for one in picked}
    assert said["breaker-one"].startswith("Stopped: breaker 2 waits for you")
    assert said["ask-criteria"].startswith("Waits for you: the acceptance criteria")
    assert said["parked-one"].startswith("Parked")
    assert said["old-landed"] == "Landed · 30d"


def test_with_25_ended_tasks_the_20_that_ended_last_have_a_row_the_newest_first() -> (
    None
):
    ended = [look(f"done-{n:02}", status="landed", since=at(n)) for n in range(25)]
    picked = picked_rows([*ended, look("still-going", status="building", since=at(99))])
    ids = [one.row_id for one in picked]
    assert ids[0] == "still-going"
    assert ids[1:-1] == [f"done-{n:02}" for n in range(20)]
    assert picked[-1].subtitle == "the board of every task · 26 tasks"


def test_an_investigation_is_its_own_state_until_a_lead_builds() -> None:
    shape = Shape(type="fix", why="a bug", track="full", then="investigation")
    investigates = record("why-crash", status="building", shape=shape).task
    assert words.state_words(investigates) == "Investigating"
    led = replace(investigates, lead="builder")
    assert words.state_words(led) == "Building"


def test_a_label_prints_and_a_long_one_ends_in_an_ellipsis() -> None:
    long_ask = record("long-one", ask="word " * 40).task
    assert len(words.label(long_ask)) == words.LABEL_WIDTH
    assert words.label(long_ask).endswith("…")
    blank = record("fix-the-login", ask="\x00\x07 ").task
    assert words.label(blank) == "Fix the login"
    assert [words.age(at(0) - dt.timedelta(seconds=s), MOMENT) for s in (30, 300)] == [
        "now",
        "5m",
    ]


class Board:
    """A stand-in for the board's opening: what it was asked to open."""

    def __init__(self) -> None:
        self.opened: list[str] = []

    def __call__(self, checkout: Path, chosen: str) -> None:
        self.opened.append(chosen)


def here_of(tmp_path: Path, terminal: FakeTerminal) -> Here:
    where = workspace(tmp_path)
    made(where, "gift-note", ask="add a gift note")
    made(where, "fix-login", ask="fix the login", status="building")
    git = ModelGit(checkout=where.checkout)
    ports = fake_ports(git, LocalForge(remote=git), terminal=terminal)
    return Here(where=where, ports=ports)


@pytest.fixture
def opened(monkeypatch: pytest.MonkeyPatch) -> Board:
    stand_in = Board()
    monkeypatch.setattr(board, "opened", stand_in)
    return stand_in


def chosen(monkeypatch: pytest.MonkeyPatch, here: Here, row_id: str | None) -> None:
    monkeypatch.setattr(looks.session_here, "bound", lambda folder: here)
    terminal = here.ports.terminal
    assert isinstance(terminal, FakeTerminal)
    terminal.picked = row_id


def test_a_pick_of_a_task_whose_session_lives_selects_that_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, opened: Board
) -> None:
    from lem.ports.terminal import Pane

    terminal = FakeTerminal(panes={"s-7": Pane(id="s-7", name="fix-login")})
    here = here_of(tmp_path, terminal)
    chosen(monkeypatch, here, "fix-login")
    monkeypatch.setattr(sessions, "live_session", lambda *_: "s-7")
    went = picking.picked(tmp_path, NOW)
    assert (went.picked, went.went, went.session) == ("fix-login", "session", "s-7")
    assert terminal.panes["s-7"].selected
    assert opened.opened == []


def test_a_pick_with_no_live_session_and_the_last_row_open_the_board(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, opened: Board
) -> None:
    here = here_of(tmp_path, FakeTerminal())
    monkeypatch.setattr(sessions, "live_session", lambda *_: None)
    chosen(monkeypatch, here, "gift-note")
    assert picking.picked(tmp_path, NOW).went == "board"
    chosen(monkeypatch, here, row.ALL)
    assert picking.picked(tmp_path, NOW).picked == row.ALL
    assert opened.opened == ["gift-note", row.ALL]


def test_escape_opens_nothing_and_says_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, opened: Board
) -> None:
    here = here_of(tmp_path, FakeTerminal())
    chosen(monkeypatch, here, None)
    assert picking.picked(tmp_path, NOW) == picking.Picked(picked=None)
    assert opened.opened == []


def test_a_terminal_that_does_not_answer_is_a_refusal_with_its_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, opened: Board
) -> None:
    class Deaf(FakeTerminal):
        def picker(self, rows: tuple[PickRow, ...], cwd: Path) -> str | None:
            raise Unanswered("agtermctl", "not on the PATH: agterm's command line tool")

    here = here_of(tmp_path, Deaf())
    monkeypatch.setattr(looks.session_here, "bound", lambda folder: here)
    with pytest.raises(Refusal) as caught:
        picking.picked(tmp_path, NOW)
    assert caught.value.code == "terminal"
    assert "not on the PATH" in caught.value.why
    assert opened.opened == []


def test_a_folder_outside_lem_a_repository_with_no_task_and_its_rows(
    tmp_path: Path,
) -> None:
    plain = tmp_path / "plain"
    plain.mkdir()
    assert refusal(lem("picker", "--list", cwd=plain))["code"] == "no-repository"
    where = workspace(tmp_path / "repo")
    assert refusal(lem("picker", "--list", cwd=where.checkout))["code"] == "no-task"
    made(where, "gift-note", ask="add a gift note")
    listed = printed(lem("picker", "--list", cwd=where.checkout))
    assert [one["id"] for one in listed] == ["gift-note", row.ALL]
    assert listed[0]["label"] == "add a gift note"
    unset = tmp_path / "unset"
    (unset / ".git").mkdir(parents=True)
    (unset / ".lem").mkdir()
    assert refusal(lem("picker", "--list", cwd=unset))["code"] == "no-settings"


def test_brackets_in_the_first_label_reach_agterm_as_a_json_row(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def pick(*_args: object, stdin: str) -> CompletedProcess[str]:
        assert json.loads(stdin) == [
            {"id": "fix-checkout", "label": "[Bug] Fix checkout", "subtitle": "Queued"},
            {"id": "other", "label": "[Bug] Fix checkout", "subtitle": "Queued"},
        ]
        return CompletedProcess([], 0, '{"result":"picked","id":"other"}', "")

    here = here_of(tmp_path, FakeTerminal())
    ports = replace_dataclass(here.ports, terminal=terminal_agterm.AgtermTerminal({}))
    here = Here(where=here.where, ports=ports)
    monkeypatch.setattr(terminal_agterm, "ctl", pick)
    found = tuple(
        PickRow(row_id=slug, label="[Bug] Fix checkout", subtitle="Queued")
        for slug in ("fix-checkout", "other")
    )
    assert picking.chosen_row(here, found) == "other"
