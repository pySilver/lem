"""What a task's page says of the owner's Inbox, the clock of a wait, and the phases of a track
(`main`'s `tests/unit/test_board_model.py`: `Inbox`, `WaitClock`, `WaitStart`, `Workspace`): each
test names the old case it stands for."""

import dataclasses
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import msgspec
from msgspec.structs import replace

from fakes.records import MOMENT
from lem.addons.inbox import messages, records
from lem.board.views import inbox_read, owed, standing
from lem.board.views.inbox_read import Inbox, Sent
from lem.board.views.panel import inbox, inbox_words, phases
from lem.model.owner.looks import Session
from lem.records.holds import BreakerHold, OwnerHold
from lem.records.journal.task import StateNoted
from lem.records.owner import Presence
from lem.records.task import Shape
from lem.records.work import Plan
from unit.board.views.small import task, world

if TYPE_CHECKING:
    from pathlib import Path

    from lem.board.views.world import World

SLUG = "gift-note"
TAILNET = "https://studio.tail4e2a.ts.net:8443/"
AWAY = Presence(away=True, since=MOMENT, words="I'm away")


def at(minutes: float) -> datetime:
    """A moment `minutes` after the records' moment."""
    return MOMENT + timedelta(minutes=minutes)


def thing(key: str = f"breaker:{SLUG}:1:20261125T102000Z", **fields: object) -> Sent:
    """A question the server sent to the Inbox, in its thread."""
    sent = Sent(
        key=key,
        task=SLUG,
        kind="breaker",
        asks=True,
        session="C1",
        thread_id="msg_01ABC",
        thread_url="http://plannotator.localhost:50026/#thread=msg_01ABC",
    )
    return replace(sent, **fields)


def record(*sent: Sent, **door: object) -> Inbox:
    """The server's record of the Inbox, which runs and has a tailnet address."""
    made = Inbox(
        running=True,
        url="http://plannotator.localhost:50026/",
        tailnet_url=TAILNET,
        sent=sent,
    )
    return replace(made, **door)


def saved(*sent: Sent, **door: object) -> bytes:
    """The Inbox add-on's wire format for a door and its sent messages."""
    entries = []
    for one in sent:
        wait = msgspec.convert(
            {
                "key": one.key,
                "task": one.task,
                "kind": one.kind,
                "since": MOMENT,
                "asks": one.asks,
                "session": one.session,
                "tip": one.tip,
            },
            records.Wait,
        )
        entries.append(
            records.Entry(
                wait=wait,
                key=one.key,
                sent=messages.Sent(
                    message_id=one.key, thread_id=one.thread_id, url=one.thread_url
                ),
            )
        )
    address = messages.Door(running=True, tailnet_url=TAILNET)
    return msgspec.json.encode(
        records.Record(door=replace(address, **door), entries=tuple(entries))
    )


def breaker_world(found: Inbox | None, presence: Presence = AWAY) -> World:
    """A building task whose breaker waits for the owner, with the Inbox's record `found`."""
    stopped = task(status="building", hold=BreakerHold(number=1, since=at(20)))
    return dataclasses.replace(world(stopped), presence=presence, inbox=found)


def said(seen: World) -> inbox.Said | None:
    """What the task's page says of the Inbox."""
    return inbox.inbox_of(seen, SLUG, owed.of_task(seen, SLUG))


def test_the_inbox_changes_nothing_while_he_is_there_while_nothing_of_the_task_went_or_for_an_old_row() -> (
    None
):
    """`main`'s Inbox.test_nothing_changes_while_he_is_there_while_nothing_of_the_task_went_
    and_for_an_old_row: the note of a session that came back is no row of the task's now; a
    thing the server could not send yet says so only while its last call failed."""
    assert said(breaker_world(record(thing()), Presence())) is None
    assert said(breaker_world(None)) is None
    assert said(breaker_world(record())) is None
    note = thing(f"session:{SLUG}", kind="session", asks=False, session=None)
    assert said(breaker_world(record(note))) is None
    unsent = thing(thread_id=None, thread_url=None)
    failed = record(unsent, problem="the send of breaker: server_error: down")
    found = said(breaker_world(failed))
    assert found is not None
    assert found.why == inbox_words.UNSENT
    assert said(breaker_world(record(unsent))) is None
    sent = said(breaker_world(record(thing())))
    assert sent is not None
    assert (sent.thread, sent.asks) == (f"{TAILNET}#thread=msg_01ABC", True)


def test_each_page_reads_the_inbox_record_afresh(tmp_path: Path) -> None:
    """`main`'s Inbox.test_the_reader_puts_the_record_into_the_model_and_reads_it_again_when_
    it_changes, changed: no model is kept between two pages; `gather` reads the record whole
    for each one."""
    assert inbox_read.read(tmp_path) is None
    (tmp_path / inbox_read.INBOX).write_bytes(saved(thing()))
    found = inbox_read.read(tmp_path)
    assert found is not None
    assert found.tailnet_url == TAILNET
    closed = saved(running=False, tailnet_url=None, why="not running")
    (tmp_path / inbox_read.INBOX).write_bytes(closed)
    again = inbox_read.read(tmp_path)
    assert again is not None
    assert again.why == "not running"


def test_the_record_is_the_servers_file_read_whole_and_each_why_has_its_words(
    tmp_path: Path,
) -> None:
    """`main`'s Inbox.test_the_record_is_the_servers_file_read_whole_and_each_why_has_its_
    words, changed: the board reads the add-on's door and deliveries. A file that does not
    read is no record."""
    whys = {
        "not installed",
        "not running",
        "not answering",
        "no tailnet address",
        "failed",
    }
    assert inbox_read.INBOX == "inbox.json"
    assert set(inbox_words.WHY) == set(inbox_words.WHY_SENT) == whys
    other = thing(f"criteria:{SLUG}", kind="criteria")
    (tmp_path / inbox_read.INBOX).write_bytes(saved(thing(), other))
    found = inbox_read.read(tmp_path)
    assert found is not None
    assert [one.key for one in found.sent] == [thing().key, f"criteria:{SLUG}"]
    (tmp_path / inbox_read.INBOX).write_text("half", encoding="utf-8")
    assert inbox_read.read(tmp_path) is None


def clocks(seen: World) -> tuple[datetime | None, datetime]:
    """The start of the task's wait as its row of Waits for you says it (None with no row),
    and as its pill and its time in this state do (`Standing.since`)."""
    found = owed.seen(seen, SLUG)
    rows = owed.of_task(seen, SLUG)
    row = rows[0].since if rows else None
    return row, standing.standing(found, rows).since


def test_a_building_task_counts_from_when_it_started_to_build() -> None:
    """`main`'s WaitClock.test_a_building_task_counts_from_when_it_started_to_build: a move to
    the status it is in writes its line alone and keeps its moment (`holds.moved`)."""
    made = task(status="building", since=at(10))
    later = StateNoted(at=at(30), status="building", line="task 2 of 3")
    journal = (*made.record.journal, later)
    seen = replace(made, record=replace(made.record, journal=journal))
    assert clocks(world(seen)) == (None, at(10))


def test_the_criteria_wait_counts_from_its_own_hold_on_the_row_and_the_pill() -> None:
    """`main`'s WaitStart.test_the_criteria_wait_counts_from_its_own_block_on_the_row_the_pill_
    and_in_this_state: one-home-folder-for-lem, whose criteria waited from their own hold,
    not from the interview's before it."""
    criteria = OwnerHold(
        on="criteria", line="the criteria wait for the owner", since=at(104)
    )
    seen = task(status="shaping", since=at(2), hold=criteria)
    assert clocks(world(seen, now=at(108))) == (at(104), at(104))


def test_a_new_session_of_a_held_task_leaves_the_clock_of_its_wait() -> None:
    """`main`'s WaitClock.test_the_same_held_line_written_again_by_a_new_session_keeps_the_
    wait_at_11_39, changed: the wait's moment is its hold's, which the command that holds the
    task sets once; a session opened since moves neither the row nor the pill."""
    criteria = OwnerHold(
        on="criteria", line="the criteria wait for the owner", since=at(104)
    )
    resumed = Session(live=True, since=at(150))
    seen = replace(task(status="shaping", since=at(2), hold=criteria), session=resumed)
    assert clocks(world(seen, now=at(155))) == (at(104), at(104))


def test_the_phases_of_the_fast_track_and_of_the_standard_track() -> None:
    """`main`'s Workspace.test_the_phases_of_the_fast_track_and_of_the_standard_track: the fast
    track's first phase is the change and its checks are its second; a build that has its plan
    is in the standard track's third."""
    small = Shape(type="fix", why="w", track="small")
    fast = task(status="landing", lead="small", shape=small).record
    found = phases.phases(fast)
    assert (found[0].name, [one.current for one in found].index(True)) == ("Change", 1)
    plan = Plan(path="docs/plans/x.md", tasks=3)
    standard = task(status="building", lead="builder", plan=plan).record
    shown = phases.phases(standard)
    assert (shown[0].name, [one.current for one in shown].index(True)) == (
        "Criteria",
        2,
    )


def test_a_blocked_task_counts_from_its_block() -> None:
    """`main`'s WaitClock.test_a_blocked_task_counts_from_the_block_that_named_its_wait,
    changed: the block is a hold with its own moment (`Blocked.since`), which the row, the
    pill and the time in this state all count from, not the build's start."""
    from lem.records.holds import Blocked

    block = Blocked(why="the fixture needs a login", fix="tell it", since=at(5))
    seen = task(status="building", since=MOMENT, hold=block)
    assert clocks(world(seen, now=at(40))) == (at(5), at(5))
    again = replace(block, why="the fixture needs a second login", since=at(30))
    other = task(status="building", since=MOMENT, hold=again)
    assert clocks(world(other, now=at(40))) == (at(30), at(30))
