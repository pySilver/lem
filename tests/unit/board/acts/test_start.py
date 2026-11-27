"""A new task from the board, from the owner's words or from a backlog item, with its session;
and the drop of a reviewer's item: what each refuses, and why."""

from datetime import timedelta
from functools import partial
from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urlsplit

import msgspec
import pytest

from fakes.records import MOMENT
from lem.app.sessions import acts, log
from lem.app.tasks import taken
from lem.board.acts import backlog, child, plugin
from lem.board.acts.notes import NOTES
from lem.kernel import clock, locks
from lem.kernel.envelope import Envelope, Refused
from lem.kernel.errors import Refusal
from lem.model.task import claim, holds
from lem.records.journal.task import OwnerAct
from lem.store import places, tasks, workspace
from unit.board.acts.acts import made, opened, read

if TYPE_CHECKING:
    from pathlib import Path

    import httpx

    from lem.board.acts.notes import Note
    from lem.records.record import Record
    from lem.records.task import Task
    from unit.board.acts.conftest import Board

WORDS = "Add the gift note to the CSV export, please"
SLUG = "add-the-gift-note-to"
REVIEWER = ".lem/state/backlog/the-export-s-check-fails-by-chance.md"
ITEM = "docs/backlog/the-receipt-reads-its-total-by-row.md"


@pytest.fixture(autouse=True)
def a_session_before(board: Board, monkeypatch: pytest.MonkeyPatch) -> None:
    """A session of the repository opened earlier, whose workspace of agterm a new task's
    session takes; the acts run later."""
    made(board, "earlier-task", status="building", lead="builder")
    opened(board, "earlier-task", MOMENT)
    monkeypatch.setattr(clock, "now", lambda: MOMENT + timedelta(hours=1))


def where_to(answer: httpx.Response) -> tuple[str, Note]:
    """The page the act went to, and its note."""
    assert answer.status_code == 303, answer.text
    address = urlsplit(answer.headers["location"])
    found = NOTES.get(parse_qs(address.query)["note"][0])
    assert found is not None
    return address.path, found


def item(board: Board, path: str) -> None:
    """A backlog item at `path`."""
    (board.checkout / path).parent.mkdir(parents=True, exist_ok=True)
    (board.checkout / path).write_text("# An item\n")


def opens(board: Board, slug: str) -> list[str]:
    """Why each session Lem opened for the task opened."""
    found = log.read(places.task_folder(board.state, slug))
    return [act.why for act in found if isinstance(act, acts.Open)]


def test_his_words_name_the_task_by_their_first_five_plain_words_and_open_its_session(
    board: Board,
) -> None:
    path, note = where_to(board.post("/start", {"words": f"  {WORDS}  "}))
    assert path == f"{board.base}/tasks/{SLUG}"
    assert note.state == "done"
    assert note.said.startswith(f"Lem opened the session {SLUG} in agterm")
    task = read(board, SLUG).task
    assert (task.ask, task.status) == (WORDS, "shaping")
    assert opens(board, SLUG) == ["new"]
    assert board.terminal.openings[-1].workspace == "W-1"
    entries = [
        one.act for one in read(board, SLUG).journal if isinstance(one, OwnerAct)
    ]
    assert entries == ["start"]


def test_the_design_s_address_starts_a_task_too(board: Board) -> None:
    path, note = where_to(board.post("/tasks", {"words": WORDS}))
    assert (path, note.state) == (f"{board.base}/tasks/{SLUG}", "done")


@pytest.mark.parametrize("enabled", (True, False))
def test_start_checks_the_plugin_the_projects_session_will_load(
    board: Board, monkeypatch: pytest.MonkeyPatch, *, enabled: bool
) -> None:
    home = board.home / "claude"
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))
    installed = home / "plugins" / "installed_plugins.json"
    installed.parent.mkdir(parents=True)
    plugin = home / "cache" / "lem"
    manifest = plugin / ".claude-plugin" / "plugin.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text('{"version": "0.1.0"}')
    installed.write_bytes(
        msgspec.json.encode(
            {
                "plugins": {
                    "lem@lem": [
                        {
                            "scope": "project",
                            "projectPath": str(board.checkout),
                            "installPath": str(plugin),
                            "version": "0.1.0",
                        }
                    ]
                }
            }
        )
    )
    (board.checkout / ".claude").mkdir()
    (board.checkout / ".claude" / "settings.local.json").write_bytes(
        msgspec.json.encode({"enabledPlugins": {"lem@lem": enabled}})
    )
    before = tasks.every(board.state)
    openings = tuple(board.terminal.openings)
    path, note = where_to(board.post("/start", {"words": WORDS}))
    if enabled:
        assert (path, note.state) == (f"{board.base}/new", "refused")
        assert "claude plugin update lem@lem" in note.said
        assert tasks.every(board.state) == before
        assert tuple(board.terminal.openings) == openings
    else:
        assert (path, note.state) == (f"{board.base}/tasks/{SLUG}", "done")


def test_the_board_uses_the_task_rule_for_the_item_holder(
    board: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    item(board, ITEM)
    holder = made(board, "item-task", status="building", backlog_item=ITEM)
    seen: list[str] = []

    def lookup(path: str, every: tuple[Record, ...]) -> Task:
        assert holder in every
        seen.append(path)
        return holder.task

    monkeypatch.setattr(claim, "item_holder", lookup, raising=False)
    path, note = where_to(board.post("/start", {"item": ITEM}))
    assert (path, note.state) == (f"{board.base}/tasks/item-task", "done")
    with pytest.raises(Refusal, match="item-task"):
        claim.claimed(holder, tasks.every(board.state), None)
    assert seen == [ITEM, ITEM]


def test_new_task_opens_even_when_a_later_journal_update_cannot_succeed(
    board: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    def busy(*args: object) -> Record:
        raise Refusal("stale", "another write came first", "try again")

    monkeypatch.setattr(tasks, "update", busy)
    path, note = where_to(board.post("/start", {"words": WORDS}))
    assert (path, note.state) == (f"{board.base}/tasks/{SLUG}", "done")
    assert opens(board, SLUG) == ["new"]
    entries = [
        entry for entry in read(board, SLUG).journal if isinstance(entry, OwnerAct)
    ]
    assert [entry.act for entry in entries] == ["start"]


def test_start_rechecks_the_item_after_drop_wins_the_claim(
    board: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    item(board, REVIEWER)
    held_during_drop: list[bool] = []

    def ran(checkout: Path, *words: str) -> Envelope:
        lock = places.locks_folder(board.state) / workspace.LOCK
        with locks.tried(lock) as available:
            held_during_drop.append(available is None)
        (checkout / words[-1]).unlink()
        return Envelope(ok=True)

    def after_drop(*args: object) -> None:
        _, note = where_to(board.post("/backlog/drop", {"item": REVIEWER}))
        assert note.state == "done"

    monkeypatch.setattr(child, "ran", ran)
    monkeypatch.setattr(taken, "checked", after_drop)
    path, note = where_to(board.post("/start", {"item": REVIEWER}))
    assert (path, note.state) == (f"{board.base}/backlog", "refused")
    assert all(task.task.backlog_item != REVIEWER for task in tasks.every(board.state))
    assert held_during_drop == [True]


def test_two_starts_of_the_same_item_open_one_task_record_one_act_and_open_one_session(
    board: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    item(board, ITEM)
    checked = plugin.checked
    fields = {"item": ITEM}
    first: list[str] = []

    def after_first_start(checkout: Path) -> None:
        monkeypatch.setattr(plugin, "checked", checked)
        path, note = where_to(board.post("/start", fields))
        assert note.state == "done"
        first.append(path)

    monkeypatch.setattr(plugin, "checked", after_first_start)
    path, note = where_to(board.post("/start", fields))
    assert [path] == first
    assert note.state == "done"
    (saved,) = [
        one for one in tasks.every(board.state) if one.task.backlog_item == ITEM
    ]
    entries = [one.act for one in saved.journal if isinstance(one, OwnerAct)]
    assert entries == ["start"]
    assert opens(board, saved.task.slug) == ["new"]


def test_a_slug_that_runs_or_ended_or_no_words_is_refused_with_why(
    board: Board,
) -> None:
    made(board, SLUG, status="building")
    made(board, "fix-the-login", status="landed")
    path, runs = where_to(board.post("/start", {"words": WORDS}))
    assert (path, runs.state) == (f"{board.base}/new", "refused")
    assert f"{SLUG} is a task already, and it is building" in runs.said
    _path, ended = where_to(board.post("/start", {"words": "fix the login"}))
    assert "fix-the-login is landed" in ended.said
    _path, empty = where_to(board.post("/start", {"words": "  ¿¡ "}))
    assert "Type a few words" in empty.said


def test_an_item_starts_as_its_stem_and_after_its_task_ended_with_2(
    board: Board,
) -> None:
    item(board, ITEM)
    path, note = where_to(board.post("/start", {"item": ITEM}))
    stem = "the-receipt-reads-its-total-by-row"
    assert (path, note.state) == (f"{board.base}/tasks/{stem}", "done")
    task = read(board, stem).task
    assert (task.ask, task.backlog_item) == (ITEM, ITEM)
    path, held = where_to(board.post("/start", {"item": ITEM}))
    assert (path, held.state) == (f"{board.base}/tasks/{stem}", "done")
    assert held.said == f"This item has a task already: {stem}, shaping."
    ended = partial(holds.moved, status="dropped", line="dropped", now=MOMENT)
    tasks.update(board.state, stem, ended, read(board, stem).revision)
    path, again = where_to(board.post("/start", {"item": ITEM}))
    assert (path, again.state) == (f"{board.base}/tasks/{stem}-2", "done")


def test_his_words_that_name_a_tracked_item_start_a_task_that_holds_it(
    board: Board,
) -> None:
    item(board, ITEM)
    words = f"Reject datetime start and end ({ITEM})"
    path, note = where_to(board.post("/start", {"words": words}))
    assert note.state == "done"
    task = read(board, path.rsplit("/", 1)[-1]).task
    assert (task.ask, task.backlog_item) == (words, ITEM)


def test_an_item_outside_the_backlog_or_gone_starts_nothing(board: Board) -> None:
    path, outside = where_to(board.post("/start", {"item": "README.md"}))
    assert (path, outside.state) == (f"{board.base}/backlog", "refused")
    _path, gone = where_to(board.post("/start", {"item": ITEM}))
    assert "the backlog item" in gone.said.lower()


def dropped_by(monkeypatch: pytest.MonkeyPatch, printed: Envelope) -> list[tuple]:
    """`lem proposals drop` replaced by one that prints `printed`; each call it got."""
    calls: list[tuple] = []

    def ran(checkout: Path, *words: str) -> Envelope:
        calls.append(words)
        return printed

    monkeypatch.setattr(child, "ran", ran)
    return calls


def test_drop_on_a_reviewers_item_runs_the_proposals_drop_and_says_what_keeps_it(
    board: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    outcome = msgspec.Raw(b'{"proposals": ["retro of 2026-11-25 #1"]}')
    calls = dropped_by(monkeypatch, Envelope(ok=True, outcome=outcome))
    path, note = where_to(board.post("/backlog/drop", {"item": REVIEWER}))
    assert (path, note.state) == (f"{board.base}/backlog", "done")
    assert "keeps the drop of retro of 2026-11-25 #1" in note.said
    assert calls == [("proposals", "drop", REVIEWER)]


def test_drop_is_refused_for_no_item_an_item_of_the_folder_and_one_a_task_holds(
    board: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = dropped_by(monkeypatch, Envelope(ok=True))
    made(board, "export-check", status="queued", backlog_item=REVIEWER)
    said = [
        where_to(board.post("/backlog/drop", {"item": shown}))[1].said
        for shown in ("", ITEM, REVIEWER)
    ]
    assert said[0].startswith("The drop names no item")
    assert "leaves it on a branch" in said[1]
    assert said[2].startswith("This item has a task already: export-check, queued.")
    assert calls == []


def test_a_refusal_of_the_proposals_drop_is_the_drops_note(
    board: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    refusal = Refused(code="not-built", why="proposals drop is not built", fix="later")
    dropped_by(monkeypatch, Envelope(ok=False, refusal=refusal))
    _path, note = where_to(board.post("/backlog/drop", {"item": REVIEWER}))
    assert (note.state, note.said) == (
        "refused",
        "Proposals drop is not built: later.",
    )
    assert note.act == backlog.ACT
