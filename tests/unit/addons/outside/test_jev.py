"""Jev's spec and the decisions wire format, with an HTTP stand-in."""

import json
from typing import TYPE_CHECKING

import httpx
import msgspec
import pytest

from fakes.command import lem
from lem.addons.jev import client, questions, reply
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from pathlib import Path

    from lem.addons.jev.records import Request

NOUL = {"type": "noul", "instructions": "Is the work done?"}
CHOICE = {
    "type": "choice",
    "instructions": "Which one?",
    "choices": {"one": "first", "two": "second"},
}
SCORED = {"choice": "one", "confidence": 0.7, "probabilities": {"one": 0.7, "two": 0.3}}


def build(state: object = "facts", **asked: object) -> Request:
    """Validate the same bytes that go through the command."""
    spec = json.dumps({"state": state, "questions": asked or {"ready": NOUL}}).encode()
    return questions.build(questions.load("-", spec), "provider-model")


def test_request_criteria_and_optional_noul_criteria() -> None:
    asked = build(
        {"fact": "the owner said yes"},
        ready=NOUL,
        picked=CHOICE,
        reviewed={**NOUL, "yes": "approved", "no": "changes"},
    )
    assert msgspec.to_builtins(asked) == {
        "model": "provider-model",
        "state": {"fact": "the owner said yes"},
        "questions": {
            "ready": NOUL,
            "picked": {
                "type": "choice",
                "instructions": "Which one?",
                "criteria": CHOICE["choices"],
            },
            "reviewed": {**NOUL, "criteria": {"true": "approved", "false": "changes"}},
        },
    }


def test_invalid_question_shapes() -> None:
    for bad in (
        {},
        {"type": "score"},
        {**CHOICE, "yes": "bad"},
        {**NOUL, "choices": {}},
        {**NOUL, "yes": "only yes"},
        {**NOUL, "yes": None, "no": None},
        {**NOUL, "yes": "ok", "no": " "},
        {**NOUL, "instructions": " "},
        {**CHOICE, "choices": {"one": "first"}},
        {**CHOICE, "choices": {"one": "one", "two": " "}},
    ):
        with pytest.raises(Refusal) as refused:
            build(named=bad)
        assert refused.value.code == "jev-spec"
        assert "named" in refused.value.why


def test_state_shape_and_exact_byte_limit() -> None:
    for invalid in (None, {}, [], "", " ", True, 1):
        with pytest.raises(Refusal, match="state"):
            build(invalid)
    assert build(["one", "two"]).state == ["one", "two"]
    overhead = len(json.dumps({"ready": NOUL}).encode())
    room = questions.LIMIT_BYTES - overhead
    assert build("x" * room).state == "x" * room
    with pytest.raises(Refusal, match="bytes"):
        build("é" * (room // 2 + 1))
    prefix = len(json.dumps({"f": ""}).encode())
    assert build({"f": "é" * ((room - prefix) // 2)}).state
    with pytest.raises(Refusal, match="bytes"):
        build({"f": "é" * ((room - prefix) // 2 + 1)})


def test_reply_checks_every_question_and_returns_cost() -> None:
    asked = build(ready=NOUL, picked=CHOICE)
    for probability in (0, 1, 0.5):
        raw = json.dumps(
            {"answers": {"ready": {"noul": probability}, "picked": SCORED}}
        ).encode()
        read = reply.read(raw, asked)
        assert read.cost is None
        assert msgspec.to_builtins(read.answers)["ready"] == {
            "type": "noul",
            "noul": probability,
        }
        assert msgspec.to_builtins(read.answers)["picked"] == {
            "type": "choice",
            **SCORED,
        }
    good = {"ready": {"noul": 1}, "picked": SCORED}
    paid = msgspec.json.encode(
        {"model": "provider-model", "answers": good, "usage": {"cost": 0.1}}
    )
    assert reply.read(paid, asked).cost == 0.1
    for bad in (
        [],
        {"ready": {"noul": 0}},
        {**good, "extra": {}},
        {**good, "ready": {"noul": True}},
        {**good, "ready": {"noul": 1.1}},
        {**good, "picked": {"choice": "one", "confidence": 0.1}},
        {**good, "picked": {**SCORED, "probabilities": {}}},
    ):
        with pytest.raises(Refusal):
            reply.read(msgspec.json.encode({"answers": bad}), asked)


def test_provider_uses_only_jev_key_and_never_sends_during_check() -> None:
    reads: list[httpx.Request] = []

    def provider(request: httpx.Request) -> httpx.Response:
        reads.append(request)
        assert str(request.url) == "https://provider.invalid/decisions"
        assert request.headers["authorization"] == "Bearer test-key"
        assert json.loads(request.content)["state"] == {"where": "test"}
        return httpx.Response(200, json={"answers": {"ready": {"noul": 1}}})

    target = client.config({"JEV_API_URL": "https://provider.invalid/decisions"})
    asked = build({"where": "test"})
    transport = httpx.MockTransport(provider)
    other_key = {"OPENROUTER_API_KEY": "unused"}
    assert client.check(asked, target, other_key).key_from is None
    with pytest.raises(Refusal, match="JEV_API_KEY"):
        client.ask(asked, target, other_key, transport)
    assert reads == []
    assert client.ask(asked, target, {"JEV_API_KEY": "test-key"}, transport).answers[
        "ready"
    ]
    assert len(reads) == 1
    assert client.config({}).url == client.URL
    for invalid in ("none", "-1", "inf"):
        with pytest.raises(Refusal, match="JEV_TIMEOUT"):
            client.config({"JEV_TIMEOUT": invalid})


def test_check_command_reads_stdin_and_rejects_non_utf8(tmp_path: Path) -> None:
    spec = json.dumps({"state": "test", "questions": {"ready": NOUL}})
    checked = lem("jev", "check", "-", stdin=spec)
    assert checked.code == 0, checked.stderr
    result = checked.result()
    assert isinstance(result, dict)
    assert result["questions"] == ["ready"]
    raw = tmp_path / "bad.json"
    raw.write_bytes(b"\xff")
    for call in (("jev", "check", str(raw)), ("jev", str(raw))):
        refused = lem(*call)
        assert refused.code == 1
        assert "utf-8" in refused.stdout.lower()
