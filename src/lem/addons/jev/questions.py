"""Check the spec and render it in the decisions endpoint's form."""

import json
from pathlib import Path

import msgspec

from lem.addons.jev.criteria import criteria, invalid
from lem.addons.jev.records import (
    Choice,
    Query,
    Question,
    Request,
    Spec,
    State,
    WireSpec,
)
from lem.kernel.errors import Refusal

# OpenRouter's long-context threshold, from its guide read 2026-11-23.
LIMIT_BYTES = 32_000


def load(path: str, standard_input: bytes) -> Spec:
    """Read one UTF-8 JSON object from a named path or stdin."""
    try:
        raw = standard_input if path == "-" else Path(path).read_bytes()
    except OSError as error:
        raise invalid(f"the owner's spec file does not read: {error}") from error
    try:
        found = msgspec.json.decode(raw.decode("utf-8"), type=WireSpec)
    except (UnicodeError, msgspec.DecodeError) as error:
        raise invalid(
            f"the owner supplied a spec that does not read: {error}"
        ) from error

    questions = {
        name: decode_question(name, raw) for name, raw in found.questions.items()
    }
    return Spec(state=found.state, questions=questions, model=found.model)


def decode_question(name: str, raw: msgspec.Raw) -> Question:
    """The owner sees the name and the formats the spec accepts."""
    try:
        return msgspec.json.decode(bytes(raw), type=Question)
    except msgspec.DecodeError as error:
        raise invalid(
            f"question {name!r} must be a choice or a noul: {error}"
        ) from error


def query(name: str, asked: Question) -> Query:
    """The endpoint's question, with its instructions and any criteria."""
    if not asked.instructions.strip():
        raise invalid(f"question {name!r} needs instructions")
    kind = "choice" if isinstance(asked, Choice) else "noul"
    return Query(
        type=kind, instructions=asked.instructions, criteria=criteria(name, asked)
    )


def state_text(state: State) -> str:
    """The text whose UTF-8 length counts against the provider's limit."""
    if not state or (isinstance(state, str) and not state.strip()):
        raise invalid("state must be a non-empty string, object or array")
    return state if isinstance(state, str) else json.dumps(state, ensure_ascii=False)


def build(spec: Spec, model: str) -> Request:
    """Check the request's text size before any call to the provider."""
    if not spec.questions:
        raise invalid(
            "questions must be a non-empty object of choice or noul questions"
        )
    named = spec.questions.items()
    queries = {name: query(name, asked) for name, asked in named}
    size = request_size(spec.state, queries)
    if size > LIMIT_BYTES:
        raise Refusal(
            "jev-size",
            f"the owner's spec uses {size} bytes, above Jev's {LIMIT_BYTES} byte limit",
            "send the full spec to a large model",
        )
    return Request(model=spec.model or model, state=spec.state, questions=queries)


def request_size(state: State, queries: dict[str, Query]) -> int:
    """The serialized questions count against the provider's text limit too."""
    packed = msgspec.to_builtins(queries)
    text = state_text(state).encode()
    encoded = json.dumps(packed).encode()
    return len(text) + len(encoded)
