"""The keys the steps asked of the records after their first build: each reads back whole, a
record written before them reads with each at its default, and the two forms that changed before
release 1.0 (`Task.after`, `TicketAct`) read as decided."""

import msgspec
import pytest

from fakes.records import MOMENT, record
from lem.records.criteria import Criteria, Waited
from lem.records.holds import BreakerHold, OwnerHold, Parked
from lem.records.journal.entry import Entry
from lem.records.journal.landing import CheckEnd, CheckWait
from lem.records.journal.sessions import (
    SessionClosed,
    SessionOpened,
    SessionStopped,
    SessionWoken,
    SessionWorked,
)
from lem.records.landing.checks import Checked, Edited, Lowered
from lem.records.landing.merge import MergeAccepted
from lem.records.landing.propose import Proposed
from lem.records.landing.record import Landing
from lem.records.landing.review import Counts, JevRead, Reviewed
from lem.records.landing.start import Based
from lem.records.record import Record
from lem.records.task import Shape
from lem.records.tickets import Ticket, TicketStep
from lem.records.work import FailedToo, StandIn

TIP = "a" * 40
BASE = "b" * 40
TREE = "c" * 40


def round_trip(made: Record) -> Record:
    """`made` written and read back."""
    return msgspec.json.decode(msgspec.json.encode(made), type=Record)


def landing() -> Landing:
    """A landing with every key a step asked for."""
    reviewed = Reviewed(
        attempt=1,
        tip=TIP,
        of="change",
        scope="whole",
        floor="read",
        kind="read",
        counts=Counts(must_fix=1, should=2, nit=3, outside=1),
        at=MOMENT,
    )
    checked = Checked(
        tip=TIP,
        tree=TREE,
        base=BASE,
        base_tree=TREE,
        inputs="0123456789ab",
        contract="feedc0ffee12",
        outcome="passed",
        lowered=(
            Lowered(path="tests/test_a.py", how="a test removed", line="def test_a"),
        ),
        edited=(Edited(path="tests/login.snap", kind="snapshot"),),
        not_covered=(".rs",),
        at=MOMENT,
    )
    proposed = Proposed(
        tip=TIP,
        base=BASE,
        contract="feedc0ffee12",
        green=True,
        who_acts="owner",
        at=MOMENT,
    )
    return Landing(
        taken=BASE,
        based=Based(
            tip=TIP, base=BASE, before=BASE, carried=True, reviewed=TIP, at=MOMENT
        ),
        checked=checked,
        reviews=(reviewed,),
        proposed=proposed,
        accepted=MergeAccepted(
            tip=TIP, at=MOMENT, queued="queued", by="merger", via="server"
        ),
        jev=(
            JevRead(key="r1.2", path="docs/backlog/a.md", score=0.4, at=MOMENT),
            JevRead(key="r1.3", not_asked="no key", at=MOMENT),
        ),
    )


def journal() -> tuple[Entry, ...]:
    """One entry of each kind a step asked for."""
    return (
        CheckWait(
            at=MOMENT,
            reason="after",
            after="other-task",
            behind_repo="shop",
            why="longer",
            unread=("blog",),
            say="the checks wait a minute after other-task",
        ),
        CheckEnd(
            at=MOMENT, outcome="passed", say="green", seconds=95, tip=TIP, taken=TIP
        ),
        SessionOpened(
            at=MOMENT, session="S1", name="fix-the-login", phase="build", why="start"
        ),
        SessionWoken(at=MOMENT, session="S1", why="status", unread=True),
        SessionWorked(at=MOMENT, session="S1", turn=MOMENT),
        SessionStopped(at=MOMENT, session="S1"),
        SessionClosed(at=MOMENT, session="S1", why="handoff"),
    )


def test_every_key_a_step_asked_for_reads_back_whole() -> None:
    stand_in = StandIn(
        seat="reviewer",
        failed="codex",
        error="login",
        at=MOMENT,
        failed_too=FailedToo(error="missing", said="no claude"),
    )
    task = record(
        after=("first", "second"),
        owner_careful=MOMENT,
        shape=Shape(type="fix", why="w", track="small", first_line="fix: the login."),
        hold=Parked(since=MOMENT, held=BreakerHold(number=2, since=MOMENT)),
        stand_ins=(stand_in,),
        criteria=Criteria(
            waited=Waited(since=MOMENT, ended_by=2),
            skip="yes",
            skip_at=MOMENT,
            changed=(MOMENT, MOMENT),
        ),
        ticket=Ticket(
            tracker="github",
            id="#42",
            repo="acme/shop",
            steps=(TicketStep(act="ticked", at=MOMENT),),
        ),
    )
    whole = msgspec.structs.replace(task, landing=landing(), journal=journal())
    assert round_trip(whole) == whole
    written = msgspec.json.encode(whole)
    for kind in ("session-open", "session-wake", "session-worked", "session-stopped"):
        assert f'"kind":"{kind}"'.encode() in written


def test_the_owners_wait_on_a_request_and_a_park_over_his_wait_read_back() -> None:
    waits = OwnerHold(
        on="request", line="the request waits for one answer", since=MOMENT
    )
    parked = Parked(since=MOMENT, words="later", held=waits)
    assert round_trip(record(hold=parked)).task.hold == parked


def test_checks_round_trip_the_path_and_kind_of_an_edited_snapshot() -> None:
    entry = {"path": "tests/login.snap", "kind": "snapshot"}
    checked = landing().checked
    written = msgspec.json.encode(checked)
    assert msgspec.json.decode(written)["edited"] == [entry]
    assert msgspec.json.decode(written, type=Checked) == checked


def test_a_record_written_before_the_asked_keys_reads_each_at_its_default() -> None:
    before = msgspec.json.encode(
        {
            "schema": 1,
            "release": "0.9.0",
            "revision": 3,
            "task": {
                "slug": "fix-the-login",
                "ask": "fix the login",
                "opened": "2026-11-25T10:00:00Z",
                "status": "queued",
                "since": "2026-11-25T10:00:00Z",
            },
        }
    )
    landing_before = (
        b'{"pushed":"'
        + TIP.encode()
        + b'","accepted":{"tip":"'
        + TIP.encode()
        + b'","at":"2026-11-25T10:00:00Z","queued":"queued"},'
        b'"checked":{"tip":"'
        + TIP.encode()
        + b'","tree":"'
        + TREE.encode()
        + b'","base":"'
        + BASE.encode()
        + b'","inputs":"x","outcome":"passed",'
        b'"at":"2026-11-25T10:00:00Z"}}'
    )
    read = msgspec.json.decode(before, type=Record)
    assert (read.task.after, read.task.owner_careful, read.task.criteria.changed) == (
        (),
        None,
        (),
    )
    found = msgspec.json.decode(landing_before, type=Landing)
    assert (found.taken, found.jev) == (None, ())
    assert found.accepted is not None
    assert (found.accepted.by, found.accepted.via) == (None, None)
    assert found.checked is not None
    assert (found.checked.contract, found.checked.base_tree, found.checked.edited) == (
        None,
        None,
        (),
    )
    entry = b'{"kind":"check-wait","at":"2026-11-25T10:00:00Z","reason":"load"}'
    wait = msgspec.json.decode(entry, type=Entry)
    assert isinstance(wait, CheckWait)
    assert (wait.after, wait.unread, wait.say) == (None, (), None)


def test_a_single_after_of_the_form_before_is_refused_as_decided() -> None:
    single = msgspec.json.encode(record()).replace(
        b'"status":"queued"', b'"status":"queued","after":"first"'
    )
    with pytest.raises(msgspec.ValidationError, match=r"\$\.task\.after"):
        msgspec.json.decode(single, type=Record)
