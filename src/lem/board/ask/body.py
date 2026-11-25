"""The bounded JSON POST from the question page."""

import json

import msgspec
from starlette.requests import ClientDisconnect, Request

from lem.app.asking.shape import Posted

LIMIT = 65536  # the card's JSON limit on main
DEPTH = 64  # unmeasured estimate for nested custom answer fields


async def read(request: Request) -> Posted | None:
    """Read a question's answer without buffering an unbounded request."""
    pieces = bytearray()
    try:
        async for next_chunk in request.stream():
            if len(pieces) + len(next_chunk) > LIMIT:
                return None
            pieces.extend(next_chunk)
    except ClientDisconnect:
        return None
    return decode(pieces)


def decode(raw: bytearray) -> Posted | None:
    """Read one answer object, with any half character made whole."""
    try:
        return converted(raw)
    except ValueError, RecursionError:
        return None


def converted(raw: bytearray) -> Posted:
    """Decode the bounded wire representation before type checks."""
    given = json.loads(raw)
    check_depth(given, DEPTH)
    clean = json.dumps(given, ensure_ascii=False, allow_nan=False)
    clean_bytes = clean.encode("utf-16", errors="surrogatepass")
    return msgspec.json.decode(
        clean_bytes.decode("utf-16", errors="replace"), type=Posted
    )


def check_depth(node: object, left: int) -> None:
    """Bound the nested JSON the card can write as an answer artifact."""
    if left < 0:
        raise ValueError("the card's answer is nested too deeply")
    if isinstance(node, dict):
        for word in node.values():
            check_depth(word, left - 1)
    if isinstance(node, list):
        for word in node:
            check_depth(word, left - 1)
