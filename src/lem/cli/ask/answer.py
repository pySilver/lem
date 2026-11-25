"""The value a question page returned, as the command prints it."""

from typing import TYPE_CHECKING

from lem.board.ask import ends, keys, receipts
from lem.cli.ask import utf8

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.questions import Answer

type Words = dict[str, object]


def submitted(raw: str | None) -> Words:
    """Take a JSON object as it came, or give another value as one text answer."""
    safe = utf8.whole(raw or "{}")
    try:
        given = utf8.decode(safe)
    except ValueError, RecursionError:
        given = None
    if isinstance(given, dict):
        return given
    text = given if isinstance(given, str) else safe
    return {
        "status": "answered",
        "answers": {"answer": {"selected": [], "labels": [], "text": text}},
    }


def label(payload: Words) -> str:
    """The shown labels, or a short description of the answer in words."""
    if payload.get("status") == "chat":
        return "A wish to talk"
    parts = payload.get("answers")
    if not isinstance(parts, dict):
        return "The answer"
    picked = [str(word) for part in parts.values() for word in labels_of(part)]
    if picked:
        return ", ".join(picked)
    if any(map(has_text, parts.values())):
        return "An answer in words"
    return "The answer"


def has_text(part: object) -> bool:
    """Whether one part is an answer in words."""
    return isinstance(part, dict) and bool(part.get("text"))


def labels_of(part: object) -> tuple[object, ...]:
    """The options named in one part of the answer."""
    if not isinstance(part, dict):
        return ()
    labels = part.get("labels")
    return tuple(labels) if isinstance(labels, list) else ()


def present(raw: Words, page: str, *, source: str = "session") -> Words:
    """Give the caller the old answer fields and the new outcome."""
    return {
        **raw,
        "outcome": raw.get("status", "answered"),
        "pageID": keys.checked(page),
        "from": source,
    }


def on_record(folder: Path, page: str, picked: Answer) -> Words:
    """The first answer, from the board or the session."""
    raw = receipts.read(keys.copies(folder, page), picked.at)
    printed = present(raw, page, source=picked.source)
    if picked.source == "board":
        printed.update(
            via=picked.via,
            device=picked.device,
            said=ends.description(picked),
        )
    return printed
