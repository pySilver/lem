"""The records of a Claude Code transcript, and its first prompt, for the `Harness` port on
Claude Code (`harness_claude`).

A transcript is one JSON record a line (`FOLDER/projects/NAME/ID.jsonl`). A record is read as
`Entry`, past every key Lem does not read, its time as text, so that a time that does not read
drops no record; a line that is no such record is passed over. The first
prompt is the first `user` record that is not `isMeta`. A task's session starts with the launch
line `Read .../.lem/state/tasks/SLUG/session.md and follow it.`, so a transcript whose first
prompt is that line, whole, is that task's (the forms read on the owner's Mac with Claude Code
2.1.294 to 2.1.330, 2026-11-22 and 23).
"""

import re
from typing import TYPE_CHECKING

import msgspec

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from pathlib import Path

# The launch line of a task's session (`app.sessions.brief`, `harness_claude.launch`).
LAUNCH = re.compile(
    r"Read [^\n]*/\.lem/state/tasks/(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)/session\.md and "
    r"follow it\."
)


class Part(msgspec.Struct, frozen=True, kw_only=True):
    """One part of a message: text, a tool's call by its name, a tool's result."""

    kind: str = msgspec.field(default="", name="type")
    text: str | None = None
    name: str | None = None


class Message(msgspec.Struct, frozen=True, kw_only=True):
    """A message: its content, and why a reply stopped."""

    body: str | tuple[Part, ...] | None = msgspec.field(default=None, name="content")
    stop_reason: str | None = None


class Entry(msgspec.Struct, frozen=True, kw_only=True):
    """One record of a transcript: its type, time and message, and whether it is meta or a
    subagent's (a sidechain)."""

    kind: str = msgspec.field(default="", name="type")
    timestamp: str | None = None
    meta: bool = msgspec.field(default=False, name="isMeta")
    sidechain: bool = msgspec.field(default=False, name="isSidechain")
    message: Message | None = None


def entry_of(line: bytes) -> Entry | None:
    """The record of one line, or None for a line that is no record."""
    try:
        return msgspec.json.decode(line, type=Entry)
    except msgspec.DecodeError:
        return None


def entries(lines: Iterable[bytes]) -> Iterator[Entry]:
    """Each line that is a record, in the order of `lines`, read as it is reached."""
    decoded = (entry_of(line) for line in lines if line.strip())
    return (entry for entry in decoded if entry is not None)


def prompt_text(entry: Entry) -> str:
    """The text of a prompt: its content when that is a text, its text blocks joined by line
    ends, and none for a prompt that holds a block of another kind (`tokens.first_prompt` on
    `main`)."""
    body = entry.message.body if entry.message else None
    if isinstance(body, str):
        return body
    parts = body or ()
    kinds = {part.kind for part in parts}
    if kinds - {"text"}:
        return ""
    return "\n".join(part.text or "" for part in parts)


def task_named(transcript: Path) -> str | None:
    """The slug of the task whose launch line is the transcript's first prompt, whole; None
    for a transcript that does not read, has no prompt, or starts with other words."""
    try:
        with transcript.open("rb") as lines:
            users = (entry for entry in entries(lines) if entry.kind == "user")
            prompt = next((entry for entry in users if not entry.meta), None)
    except OSError:
        return None
    found = LAUNCH.fullmatch(prompt_text(prompt)) if prompt else None
    return found["slug"] if found else None
