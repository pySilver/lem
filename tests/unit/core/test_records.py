"""The records: every struct writes the JSON it reads back, a union is told apart by its
`kind`, a key a newer release adds is read past, and a default is left out of the file."""

import msgspec
import pytest

from fakes.records import MOMENT, record
from lem.records.decisions import Breaker, Taken
from lem.records.holds import Blocked, BreakerHold, OwnerHold, Parked, ReleaseHold
from lem.records.journal.entry import Entry
from lem.records.journal.landing import CheckWait
from lem.records.journal.merge import RefusalNoted
from lem.records.landing.merge import MergeIntent, Refused
from lem.records.landing.record import Landing, Pull
from lem.records.record import Record

SHA = "a" * 40


def test_every_hold_reads_back_as_its_own_kind() -> None:
    holds = (
        OwnerHold(on="criteria", line="the criteria wait for the owner", since=MOMENT),
        BreakerHold(number=2, since=MOMENT),
        Blocked(why="the base is red", fix="wait", after="repair-base", since=MOMENT),
        Parked(since=MOMENT),
        ReleaseHold(
            began="0.9.0", running="1.1.0", say="drop, then resume", since=MOMENT
        ),
    )
    for hold in holds:
        written = msgspec.json.encode(record(hold=hold))
        assert msgspec.json.decode(written, type=Record).task.hold == hold


def test_a_decision_and_a_journal_entry_carry_their_kind() -> None:
    taken = Taken(id=1, at=MOMENT, what="w", chose="c", why="y", by="lead")
    breaker = Breaker(
        id=2,
        at=MOMENT,
        cause="criteria",
        what="t",
        document="breaker-2.md",
        handoff="handoff.md",
    )
    wait = CheckWait(at=MOMENT, reason="load", load=12.5, start_below=8.0)
    refusal = Refused(
        tip=SHA, source="github", kind="rule", line="no", by="merger", at=MOMENT
    )
    noted = RefusalNoted(at=MOMENT, refusal=refusal)
    whole = msgspec.structs.replace(
        record(decisions=(taken, breaker)), journal=(wait, noted)
    )
    written = msgspec.json.encode(whole)
    assert b'"kind":"taken"' in written
    assert b'"kind":"check-wait"' in written
    assert msgspec.json.decode(written, type=Record) == whole
    assert (
        msgspec.json.decode(
            b'{"kind":"refused","at":"2026-11-25T10:00:00Z","refusal":'
            + msgspec.json.encode(refusal)
            + b"}",
            type=Entry,
        )
        == noted
    )


def test_an_unknown_kind_of_entry_is_a_refusal_to_read() -> None:
    with pytest.raises(msgspec.ValidationError, match="Invalid value 'gone'"):
        msgspec.json.decode(b'{"kind":"gone","at":"2026-11-25T10:00:00Z"}', type=Entry)


def test_a_landing_with_a_merge_intent_reads_back_whole() -> None:
    intent = MergeIntent(tip=SHA, by="owner", via="board", at=MOMENT)
    landing = Landing(
        round=2,
        phase="open",
        pull=Pull(number=7, url="https://example.com/7", title="Fix the login"),
        pushed=SHA,
        intent=intent,
    )
    whole = msgspec.structs.replace(record(), landing=landing)
    assert msgspec.json.decode(msgspec.json.encode(whole), type=Record) == whole


def test_a_default_is_left_out_of_the_file() -> None:
    written = msgspec.json.decode(msgspec.json.encode(record()))
    assert sorted(written["task"]) == ["ask", "opened", "since", "slug", "status"]
    assert sorted(written) == [
        "journal",
        "landing",
        "release",
        "revision",
        "schema",
        "task",
    ]


def test_a_record_is_a_value_that_no_one_changes_in_place() -> None:
    made = record()
    field = "status"
    with pytest.raises(AttributeError):
        setattr(made.task, field, "dropped")
