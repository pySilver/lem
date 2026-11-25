"""The envelope every command prints (the design's part 5), and the refusal it carries."""

import msgspec
import pytest

from lem.kernel.envelope import Envelope, Failed, Next, Refused
from lem.kernel.errors import Refusal


def test_a_done_command_prints_ok_its_result_a_line_and_what_comes_next() -> None:
    printed = msgspec.json.encode(
        Envelope(
            ok=True,
            outcome=msgspec.Raw(b'{"slug":"a-task"}'),
            say="The task waits for its checks.",
            following=Next(act="run", command="lem land next a-task"),
        )
    )
    assert printed == (
        b'{"ok":true,"result":{"slug":"a-task"},'
        b'"say":"The task waits for its checks.",'
        b'"next":{"do":"run","command":"lem land next a-task"}}'
    )


def test_a_refusal_prints_its_code_why_and_fix_and_nothing_else() -> None:
    printed = msgspec.json.encode(
        Envelope(
            ok=False,
            refusal=Refused(code="stale", why="the record moved", fix="read it again"),
        )
    )
    assert printed == (
        b'{"ok":false,"refusal":'
        b'{"code":"stale","why":"the record moved","fix":"read it again"}}'
    )


def test_a_fault_prints_one_line_and_where_its_traceback_is() -> None:
    printed = msgspec.json.encode(
        Envelope(ok=False, fault=Failed(line="lem broke", log="/home/lem.log"))
    )
    assert printed == b'{"ok":false,"fault":{"line":"lem broke","log":"/home/lem.log"}}'


def test_next_leaves_out_what_it_does_not_say() -> None:
    assert msgspec.json.encode(Next(act="done")) == b'{"do":"done"}'
    assert msgspec.json.encode(
        Next(act="spawn", job="review", paths=("a.md", "b.md"))
    ) == (b'{"do":"spawn","job":"review","paths":["a.md","b.md"]}')


def test_an_envelope_with_no_result_reads_back_as_it_was_printed() -> None:
    printed = b'{"ok":true,"next":{"do":"wait","until":"checks","why":"load"}}'
    read = msgspec.json.decode(printed, type=Envelope)
    assert read.following == Next(act="wait", until="checks", why="load")
    assert msgspec.json.encode(read) == printed


def test_a_reader_of_a_result_takes_the_json_whole() -> None:
    # msgspec reads a Raw on its own, never as one side of `Raw | None`: a test or a caller that
    # needs `result` decodes the printed document untyped.
    printed = b'{"ok":true,"result":[1,2]}'
    with pytest.raises(msgspec.ValidationError, match="Expected `null`"):
        msgspec.json.decode(printed, type=Envelope)
    assert msgspec.json.decode(printed)["result"] == [1, 2]


def test_an_act_outside_the_five_is_refused_on_reading() -> None:
    with pytest.raises(msgspec.ValidationError, match="do"):
        msgspec.json.decode(b'{"ok":true,"next":{"do":"jump"}}', type=Envelope)


def test_a_refusal_keeps_its_three_parts_and_says_why() -> None:
    refusal = Refusal("stale", "the record moved", "read it again")
    assert (refusal.code, refusal.why, refusal.fix) == (
        "stale",
        "the record moved",
        "read it again",
    )
    assert str(refusal) == "the record moved"
