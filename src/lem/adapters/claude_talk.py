"""The turns of the Claude Code session a command runs in, for `lem session talk`
(`session.transcript_turns` and `session.transcript_file` on `main`; the form is the harness's,
`skills/lem/harness/claude-code.md`).

The session's transcript is `projects/*/ID.jsonl` under `CLAUDE_CONFIG_DIR`, else `~/.claude`,
with ID the `CLAUDE_CODE_SESSION_ID` that Claude Code gives the Bash tool. The owner's turn is a
`user` record whose `origin.kind` is `human`, with no `isMeta` (the text `/lem` loads) and no
`isCompactSummary`; a `/lem` line is kept as he typed it. The agent's turn is the text of the
`assistant` records between two prompts; a tool's call and its result are no words, and a
subagent's record is no turn of this session. A transcript that names no prompt's origin is of
another form, and refused.
"""

import re
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import msgspec

from lem.adapters.claude_transcript import Part
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from collections.abc import Mapping

SESSION = re.compile(r"[A-Za-z0-9-]+")
COMMAND = re.compile(r"<command-name>(?P<name>.*?)</command-name>", re.DOTALL)
ARGS = re.compile(r"<command-args>(?P<args>.*?)</command-args>", re.DOTALL)


class Origin(msgspec.Struct, frozen=True, kw_only=True):
    """Where a prompt came from: `human` for the owner's."""

    kind: str = ""


class Said(msgspec.Struct, frozen=True, kw_only=True):
    """A message's content."""

    body: str | tuple[Part, ...] | None = msgspec.field(default=None, name="content")


class Record(msgspec.Struct, frozen=True, kw_only=True):
    """One record of the transcript, as the talk reads it."""

    kind: str = msgspec.field(default="", name="type")
    timestamp: str | None = None
    meta: bool = msgspec.field(default=False, name="isMeta")
    sidechain: bool = msgspec.field(default=False, name="isSidechain")
    compacted: bool = msgspec.field(default=False, name="isCompactSummary")
    origin: Origin | None = None
    message: Said | None = None

    def texts(self) -> tuple[str, ...]:
        """The text blocks of the message."""
        body = self.message.body if self.message else None
        parts = body if isinstance(body, tuple) else ()
        return tuple(part.text or "" for part in parts if part.kind == "text")

    def prompt(self) -> str:
        """The text of a prompt record."""
        body = self.message.body if self.message else None
        return body if isinstance(body, str) else "\n".join(self.texts())


class Turn(msgspec.Struct, frozen=True, kw_only=True):
    """A turn: the owner's or the agent's, when, its words, and a slash command's
    arguments."""

    who: Literal["owner", "lem"]
    at: str | None
    text: str
    args: str | None = None


def own_transcript(environ: Mapping[str, str]) -> Path:
    """The transcript of the Claude Code session this command runs in."""
    session = environ.get("CLAUDE_CODE_SESSION_ID", "").strip()
    if not SESSION.fullmatch(session):
        raise Refusal(
            "no-claude-session",
            "CLAUDE_CODE_SESSION_ID names no session of Claude Code here",
            "run lem session talk from the Claude Code session where the owner asked",
        )
    named = environ.get("CLAUDE_CONFIG_DIR")
    home = Path(named) if named else Path(environ["HOME"]) / ".claude"
    found = sorted(home.glob(f"projects/*/{session}.jsonl"))
    if len(found) != 1:
        raise Refusal(
            "no-transcript",
            f"no transcript, or more than one, carries the session {session} under {home}",
            "run this from the Claude Code session where the owner asked",
        )
    return found[0]


def typed(record: Record) -> tuple[str, str | None]:
    """The words the owner typed, and a slash command's arguments: a `/lem` line is kept as
    he typed it, `/lem ARGS` (Claude Code names a plugin's skill `/lem:lem`)."""
    text = record.prompt().strip()
    name = COMMAND.search(text)
    if name is None or not text.startswith(("<command-message>", "<command-name>")):
        return text, None
    given = ARGS.search(text)
    args = given["args"].strip() if given else ""
    command = command_of(name["name"])
    return (f"{command} {args}" if args else command), args


def command_of(name: str) -> str:
    """A slash command's name as he typed it: a plugin's skill named for its plugin is the
    plugin's name."""
    plugin, colon, skill = name.strip().lstrip("/").partition(":")
    return f"/{plugin}" if colon and plugin == skill else name.strip()
