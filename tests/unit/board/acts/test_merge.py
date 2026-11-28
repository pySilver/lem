"""The owner's approval of a merge from its confirm step (amendment A4: the button says Approve):
only with the confirm and the commit proposed now, its merge in a thread of its own as the
owner's word through the board, one at a time for a task, and his approval that stands through a
moved base said as standing, with no merge started."""

import threading
import time
from typing import TYPE_CHECKING

import msgspec
import pytest
from msgspec.structs import replace

from fakes.records import MOMENT, record
from lem.app.landing import merge_lock, reconcile
from lem.app.owner import forge
from lem.app.sessions.here import bound
from lem.board.acts import merging, noting
from lem.board.acts.notes import NOTES
from lem.board.duties import context, merge_count
from lem.board.duties.memory import MEMORY
from lem.kernel import clock, locks
from lem.kernel.errors import Refusal
from lem.model.criteria import contract
from lem.model.landing import merge_standing
from lem.records.holds import BreakerHold, Parked
from lem.records.landing.merge import MergeAccepted, MergeIntent, Refused
from lem.records.landing.propose import MergeRead, Proposed, Standing
from lem.records.landing.record import Landing, Pull
from lem.store import places, tasks
from unit.board.acts.acts import SLUG, made, note_of, read
from unit.board.acts.conftest import PHONE
from unit.board.pages.markup import Parsed

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

    def run(folder: Path, slug: str, asked: Asked, *, before_call: object) -> None:
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
        f"{SLUG} is not open for a merge now: it is building. Read the task's page again.",
    )


def test_a_parked_task_refuses_a_click_from_an_open_confirm_page(
    board: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened_pull(board)
    before = read(board)
    parked = tasks.update(
        board.state,
        SLUG,
        lambda one: replace(one, task=replace(one.task, hold=Parked(since=MOMENT))),
        before.revision,
    )
    calls: list[Asked] = []
    monkeypatch.setattr(merging.merge, "run", accepting(calls))
    note = settled(board, token_of(board, {"tip": TIP, "confirm": "yes"}))
    assert note.state == "refused"
    assert note.said == f"The task is parked. Resume it with /lem resume {SLUG}."
    assert read(board) == parked
    assert calls == []


def test_a_stale_merge_tip_tells_the_owner_to_read_the_confirm_step_again(
    board: Board,
) -> None:
    opened_pull(board)
    note = note_of(board.post(MERGE, {"tip": BASE, "confirm": "yes"}))
    assert note.state == "refused"
    assert note.said.endswith("Read the confirm step again.")


def test_a_known_conflict_refuses_a_fresh_approval_before_it_can_stand(
    board: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened_pull(board)
    look = forge.Look(seen={SLUG: forge.Seen(head=TIP, mergeable=forge.CONFLICTING)})
    (board.state / forge.LOOK).write_bytes(msgspec.json.encode(look))
    before = read(board)
    calls: list[Asked] = []
    monkeypatch.setattr(merging.merge, "run", accepting(calls))
    token = token_of(board, {"tip": TIP, "confirm": "yes"})
    note = settled(board, token)
    assert note.state == "refused"
    assert "conflicting" in note.said
    assert "brings it onto the base" in note.said
    assert read(board) == before
    assert calls == []


def test_an_approval_already_on_record_stands_when_the_forge_reports_a_conflict(
    board: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened_pull(board)
    before = read(board)
    assert before.landing is not None
    reasons = merge_standing.digest_of(
        merge_standing.reasons_now(before), contract.mark(before.task)
    )
    standing = Standing(tip=TIP, reasons_digest=reasons, by_act="board", at=MOMENT)
    landing = replace(before.landing, standing=standing)
    saved = tasks.update(
        board.state,
        SLUG,
        lambda record: replace(record, landing=landing),
        before.revision,
    )
    look = forge.Look(seen={SLUG: forge.Seen(head=TIP, mergeable=forge.CONFLICTING)})
    (board.state / forge.LOOK).write_bytes(msgspec.json.encode(look))
    calls: list[Asked] = []
    monkeypatch.setattr(merging.merge, "run", accepting(calls))
    note = settled(board, token_of(board, {"tip": TIP, "confirm": "yes"}))
    assert note.state == "stands"
    assert read(board) == saved
    assert calls == []


def test_githubs_refusal_of_the_current_tip_allows_a_fresh_approval(
    board: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened_pull(board)
    before = read(board)
    assert before.landing is not None
    refused = Refused(
        tip=TIP,
        source="github",
        kind="rule",
        line="checks required",
        by="owner",
        at=MOMENT,
    )
    reasons = merge_standing.digest_of(
        merge_standing.reasons_now(before), contract.mark(before.task)
    )
    standing = Standing(tip=TIP, reasons_digest=reasons, by_act="board", at=MOMENT)
    landing = replace(before.landing, standing=standing)
    tasks.update(
        board.state,
        SLUG,
        lambda record: reconcile.taken(replace(record, landing=landing), found=refused),
        before.revision,
    )
    calls: list[Asked] = []
    monkeypatch.setattr(merging.merge, "run", accepting(calls))
    token = token_of(board, {"tip": TIP, "confirm": "yes"})
    note = settled(board, token)
    assert note.state == "done", note.said
    assert [asked.tip for asked in calls] == [TIP]


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


@pytest.mark.parametrize(("feature", "subject"), [(False, None), (True, TITLE)])
def test_where_the_history_keeps_commits_only_a_features_squash_gets_its_title(
    board: Board, monkeypatch: pytest.MonkeyPatch, *, feature: bool, subject: str | None
) -> None:
    keep = '[branch]\nbase = "main"\nhistory = "keep"\n'
    (board.checkout / ".lem" / "settings.toml").write_text(keep)
    opened_pull(board)
    if feature:
        made(board, "a-part", part_of=SLUG, status="landed")
        found = read(board)

        def joined(record: Record) -> Record:
            return replace(record, task=replace(record.task, after=("a-part",)))

        tasks.update(board.state, SLUG, joined, found.revision)
    calls: list[Asked] = []
    monkeypatch.setattr(merging.merge, "run", accepting(calls))
    settled(board, token_of(board, {"tip": TIP, "confirm": "yes"}))
    (asked,) = calls
    assert asked.subject == subject


def test_a_second_press_while_the_merge_runs_gets_that_merges_note(
    board: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened_pull(board)
    gate = threading.Event()
    calls: list[str] = []

    def waits(folder: Path, slug: str, asked: Asked, *, before_call: object) -> None:
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


def test_a_press_while_a_duty_holds_the_merge_slot_writes_no_act(board: Board) -> None:
    opened_pull(board)
    before = read(board)
    kept = MEMORY.of(board.checkout)
    release = threading.Event()
    worker = threading.Thread(target=release.wait, args=(10,))
    assert kept.start_merge(SLUG, worker)
    try:
        token = token_of(board, {"tip": TIP, "confirm": "yes"})
        note = settled(board, token)
        assert (note.state, note.said) == ("refused", "Lem already runs this merge.")
        assert read(board) == before
    finally:
        release.set()
        worker.join()


def test_the_merge_line_counts_refund_while_its_board_approval_waits(
    board: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    refund = "refund"
    first = "receipt"
    calling = MergeRead(tip=TIP, base=BASE, base_tree=BASE, verdict="call", at=MOMENT)
    landing = Landing(phase="open", pull=PULL, proposed=PROPOSED, reads=(calling,))
    tasks.create(board.state, replace(record(refund, status="open"), landing=landing))
    lock = places.locks_folder(board.state) / merge_lock.LOCK
    reached = threading.Event()

    def waits(folder: Path, slug: str, asked: Asked, *, before_call: object) -> None:
        with locks.tried(lock) as found:
            assert found is None
            reached.set()
        with locks.held(lock):
            pass

    monkeypatch.setattr(merging.merge, "run", waits)
    kept = MEMORY.of(board.checkout)
    duty = context.Duty(name="shop", here=bound(board.checkout), now=MOMENT, kept=kept)
    intent = MergeIntent(tip=BASE, by="merger", via="server", at=MOMENT)
    assert merge_count.waited(duty, first, intent).waiting == 0
    try:
        with locks.held(lock):
            note = note_of(
                board.post(f"/tasks/{refund}/merge", {"tip": TIP, "confirm": "yes"})
            )
            assert note.state == "running"
            assert reached.wait(5)
            waited = merge_count.waited(duty, first, intent)
            assert (waited.waiting, waited.behind) == (1, (refund,))
    finally:
        if worker := kept.merging.get(refund):
            worker.join()
    assert merge_count.waited(duty, first, intent).waiting == 0


def test_a_stale_approval_note_is_inside_the_phone_task_panel(board: Board) -> None:
    opened_pull(board)
    response = board.post(MERGE, {"tip": BASE, "confirm": "yes"})
    frame = board.client.get(
        response.headers["location"],
        headers={
            "Turbo-Frame": "task",
            "User-Agent": PHONE,
        },
    )
    assert frame.status_code == 200
    panel = Parsed(frame.text).root.one(id_="panel")
    note = panel.one(cls="act-note")
    assert note.has("a-bad")
    assert "Read the confirm step again." in note.words()


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

    def refused(folder: Path, slug: str, asked: Asked, *, before_call: object) -> None:
        kept.append(Standing(tip=TIP, reasons_digest="d", by_act="board", at=MOMENT))
        raise Refusal("base", "origin's main moved after the checks ran", "read it")

    monkeypatch.setattr(merging.merge, "run", refused)
    monkeypatch.setattr(
        merge_standing, "standing_of", lambda record: kept[0] if kept else None
    )
    token = token_of(board, {"tip": TIP, "confirm": "yes"})
    assert settled(board, token).state == "stands"


def test_a_standing_approval_says_checks_run_on_the_rebase_and_red_leaves_the_line(
    board: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened_pull(board)
    standing = Standing(tip=TIP, reasons_digest="d", by_act="board", at=MOMENT)
    monkeypatch.setattr(merge_standing, "standing_of", lambda record: standing)
    note = note_of(board.post(MERGE, {"tip": TIP, "confirm": "yes"}))
    assert note.state == "stands"
    assert "checks the rebased task before it merges" in note.said
    assert "If the checks fail, the task leaves the merge line." in note.said


@pytest.mark.parametrize("fails", ("journal", "thread"))
def test_a_failed_merge_start_refuses_that_click_and_the_next_one_can_run(
    board: Board, monkeypatch: pytest.MonkeyPatch, fails: str
) -> None:
    opened_pull(board)
    calls: list[Asked] = []
    monkeypatch.setattr(merging.merge, "run", accepting(calls))

    def no_write(*args: object) -> None:
        raise Refusal("stale", "the task record changed", "approve again")

    class StoppedThread:
        def __init__(self, **kwargs: object) -> None:
            pass

        def start(self) -> None:
            raise RuntimeError("cannot start thread")

    fields = {"tip": TIP, "confirm": "yes"}
    with monkeypatch.context() as patch:
        if fails == "journal":
            patch.setattr(noting, "noted", no_write)
        else:
            # Starlette's own threads must still start.
            patch.setattr("lem.board.acts.merge.Thread", StoppedThread)
        token = token_of(board, fields)
        refused = settled(board, token)
        assert refused.state == "refused"
        assert calls == []
        assert NOTES.running((str(board.checkout), SLUG)) is None
    retry = token_of(board, fields)
    assert retry != token
    assert settled(board, retry).state == "done"
    assert len(calls) == 1


def test_any_other_refusal_of_the_merge_is_its_note(
    board: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened_pull(board)

    def refused(folder: Path, slug: str, asked: Asked, *, before_call: object) -> None:
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

    def waits(folder: Path, slug: str, asked: Asked, *, before_call: object) -> None:
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
