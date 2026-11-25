"""The owner's approval of a merge from its confirm step (amendment A4: the button says Approve):
only with the confirm and the commit proposed now, its merge in a thread of its own as the
owner's word through the board, one at a time for a task, and his approval that stands through a
moved base said as standing, with no merge started."""

import threading
import time
from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from fakes.records import MOMENT
from lem.board.acts import merging
from lem.board.acts.notes import NOTES
from lem.kernel import clock
from lem.kernel.errors import Refusal
from lem.model.landing import merge_standing
from lem.records.holds import BreakerHold
from lem.records.landing.merge import MergeAccepted
from lem.records.landing.propose import Proposed, Standing
from lem.records.landing.record import Landing, Pull
from lem.store import tasks
from unit.board.acts.acts import SLUG, made, note_of, read

if TYPE_CHECKING:
    from pathlib import Path

    from lem.board.acts.notes import Note
    from lem.model.landing.merge_asked import Asked
    from lem.records.record import Record
    from unit.board.acts.conftest import Board

TIP = "a" * 40
BASE = "b" * 40
MERGE = f"/tasks/{SLUG}/merge"
TITLE = "feat: the gift note in the export"
PROPOSED = Proposed(tip=TIP, base=BASE, green=True, who_acts="owner", at=MOMENT)
PULL = Pull(number=44, url="https://github.com/o/r/pull/44", title=TITLE)


def opened_pull(board: Board) -> None:
    """A task whose pull request is open, proposed at TIP."""
    landing = Landing(phase="open", pull=PULL, proposed=PROPOSED)
    made(board, status="open")
    record = read(board)
    tasks.update(
        board.state,
        SLUG,
        lambda found: replace(found, landing=landing),
        record.revision,
    )


def settled(board: Board, token: str) -> Note:
    """The note of `token` once the task's merge no longer runs."""
    key = (str(board.checkout), SLUG)
    deadline = time.monotonic() + 10
    while NOTES.running(key) is not None and time.monotonic() < deadline:
        time.sleep(0.01)
    assert NOTES.running(key) is None
    note = NOTES.get(token)
    assert note is not None
    return note


def token_of(board: Board, fields: dict[str, str]) -> str:
    """The token of the note the approval's 303 names."""
    answer = board.post(MERGE, fields)
    assert answer.status_code == 303
    return answer.headers["location"].rsplit("note=", 1)[1]


def accepting(calls: list[Asked]) -> object:
    """A landing's merge that GitHub takes into its queue."""

    def run(folder: Path, slug: str, asked: Asked) -> None:
        calls.append(asked)
        record = tasks.read(folder / ".lem" / "state", slug)
        assert record.landing is not None
        took = MergeAccepted(tip=TIP, at=MOMENT, queued="the merge queue")

        def change(found: Record) -> Record:
            return replace(found, landing=replace(record.landing, accepted=took))

        tasks.update(folder / ".lem" / "state", slug, change, record.revision)

    return run


@pytest.mark.parametrize(
    ("fields", "said"),
    [
        ({"tip": TIP}, "A merge runs only from its confirm step"),
        ({"tip": "c" * 40, "confirm": "yes"}, "The branch was proposed again"),
    ],
)
def test_a_merge_runs_only_from_its_confirm_step_and_for_the_tip_proposed_now(
    board: Board,
    monkeypatch: pytest.MonkeyPatch,
    fields: dict[str, str],
    said: str,
) -> None:
    opened_pull(board)
    calls: list[Asked] = []
    monkeypatch.setattr(merging.merge, "run", accepting(calls))
    note = note_of(board.post(MERGE, fields))
    assert note.state == "refused"
    assert note.said.startswith(said)
    assert calls == []


def test_a_task_that_is_not_open_is_not_merged(board: Board) -> None:
    made(board, status="building")
    note = note_of(board.post(MERGE, {"tip": TIP, "confirm": "yes"}))
    assert (note.state, note.said) == (
        "refused",
        f"{SLUG} is not open for a merge now: it is building.",
    )


def test_his_approval_merges_as_his_word_through_the_board_and_says_what_came_of_it(
    board: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened_pull(board)
    calls: list[Asked] = []
    monkeypatch.setattr(merging.merge, "run", accepting(calls))
    token = token_of(board, {"tip": TIP, "confirm": "yes"})
    note = settled(board, token)
    assert (note.state, note.said) == (
        "done",
        "GitHub took the merge of pull request #44 and holds it: the merge queue.",
    )
    (asked,) = calls
    assert (asked.by, asked.via, asked.tip, asked.standing, asked.subject) == (
        "owner",
        "board",
        TIP,
        False,
        TITLE,
    )


def test_a_second_press_while_the_merge_runs_gets_that_merges_note(
    board: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened_pull(board)
    gate = threading.Event()
    calls: list[str] = []

    def waits(folder: Path, slug: str, asked: Asked) -> None:
        calls.append(slug)
        gate.wait(10)

    monkeypatch.setattr(merging.merge, "run", waits)
    first = token_of(board, {"tip": TIP, "confirm": "yes"})
    second = token_of(board, {"tip": TIP, "confirm": "yes"})
    running = NOTES.get(first)
    assert running is not None
    assert (second, running.state) == (first, "running")
    gate.set()
    settled(board, first)
    assert calls == [SLUG]


def test_a_press_while_his_approval_stands_starts_nothing_and_says_it_stands(
    board: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened_pull(board)
    standing = Standing(tip=TIP, reasons_digest="d", by_act="board", at=MOMENT)
    monkeypatch.setattr(merge_standing, "standing_of", lambda record: standing)
    calls: list[Asked] = []
    monkeypatch.setattr(merging.merge, "run", accepting(calls))
    note = note_of(board.post(MERGE, {"tip": TIP, "confirm": "yes"}))
    assert note.state == "stands"
    assert note.said.startswith(
        f"Your approval of pull request #44 at {TIP[:12]} stands"
    )
    assert calls == []


def test_a_merge_the_moved_base_refused_keeps_his_approval_standing(
    board: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened_pull(board)
    kept: list[Standing] = []

    def refused(folder: Path, slug: str, asked: Asked) -> None:
        kept.append(Standing(tip=TIP, reasons_digest="d", by_act="board", at=MOMENT))
        raise Refusal("base", "origin's main moved after the checks ran", "read it")

    monkeypatch.setattr(merging.merge, "run", refused)
    monkeypatch.setattr(
        merge_standing, "standing_of", lambda record: kept[0] if kept else None
    )
    token = token_of(board, {"tip": TIP, "confirm": "yes"})
    assert settled(board, token).state == "stands"


def test_any_other_refusal_of_the_merge_is_its_note(
    board: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened_pull(board)

    def refused(folder: Path, slug: str, asked: Asked) -> None:
        raise Refusal("github", "GitHub refused the merge", "act on GitHub")

    monkeypatch.setattr(merging.merge, "run", refused)
    token = token_of(board, {"tip": TIP, "confirm": "yes"})
    after = settled(board, token)
    assert (after.state, after.said) == (
        "refused",
        "GitHub refused the merge: act on GitHub.",
    )


def test_while_a_merge_runs_another_act_is_taken_and_the_merge_says_it_runs(
    board: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened_pull(board)
    hold = BreakerHold(number=1, since=MOMENT)
    made(board, "other-task", status="building", hold=hold)
    gate = threading.Event()

    def waits(folder: Path, slug: str, asked: Asked) -> None:
        gate.wait(10)

    monkeypatch.setattr(merging.merge, "run", waits)
    token = token_of(board, {"tip": TIP, "confirm": "yes"})
    key = f"breaker:other-task:1:{clock.compact(MOMENT)}"
    fields = {"key": key, "option": "help", "words": "keep going"}
    answered = note_of(board.post("/tasks/other-task/answer", fields))
    running = NOTES.get(token)
    assert running is not None
    assert (answered.state, running.state) == ("done", "running")
    assert running.said.startswith("Lem merges pull request #44 on your approval.")
    gate.set()
    settled(board, token)
