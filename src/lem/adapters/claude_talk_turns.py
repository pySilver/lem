"""The turns of a Claude Code transcript, oldest first, for `lem session talk` (`claude_talk` says
the form): the owner's typed turns and the agent's text between two prompts."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import msgspec

from lem.adapters.claude_talk import Record, Turn, typed
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class Reader:
    """The turns read so far, whether the agent's turn is open, and how many prompts and
    origins were seen."""

    turns: list[Turn] = field(default_factory=list)
    speaking: bool = False
    prompts: int = 0
    origins: int = 0

    def take(self, record: Record) -> None:
        """Read one record into the turns."""
        if record.sidechain:
            return
        if record.kind == "assistant":
            self.agent(record)
        elif record.kind == "user" and not tool_result(record):
            self.prompt(record)

    def agent(self, record: Record) -> None:
        """An agent's record: its text joins the agent's open turn, or opens one."""
        texts = (text.strip() for text in record.texts())
        words = "\n\n".join(filter(None, texts))
        if not words:
            return
        if self.speaking:
            last = self.turns[-1]
            self.turns[-1] = msgspec.structs.replace(
                last, text=f"{last.text}\n\n{words}"
            )
            return
        self.turns.append(Turn(who="lem", at=record.timestamp, text=words))
        self.speaking = True

    def prompt(self, record: Record) -> None:
        """A prompt: it ends the agent's turn; the owner's own is a turn."""
        self.speaking = False
        self.prompts += 1
        self.origins += record.origin is not None
        human = record.origin is not None and record.origin.kind == "human"
        if record.meta or record.compacted or not human:
            return
        text, args = typed(record)
        if text:
            self.turns.append(
                Turn(who="owner", at=record.timestamp, text=text, args=args)
            )


def tool_result(record: Record) -> bool:
    """Whether a user record is a tool's result, which is no prompt."""
    body = record.message.body if record.message else None
    parts = body if isinstance(body, tuple) else ()
    return any(part.kind == "tool_result" for part in parts)


def record_of(line: bytes) -> Record | None:
    """One line of the transcript, or None for one that is no record."""
    try:
        return msgspec.json.decode(line, type=Record)
    except msgspec.DecodeError:
        return None


def turns(path: Path) -> tuple[Turn, ...]:
    """The turns of the transcript at `path`; refused when it names no prompt's origin."""
    reader = Reader()
    for line in path.read_bytes().splitlines():
        found = record_of(line)
        if found is not None:
            reader.take(found)
    if reader.prompts and not reader.origins:
        raise Refusal(
            "transcript-form",
            f"{path} names no prompt's origin, so the owner's turns cannot be told from the rest",
            "give the new session the talk by hand",
        )
    return tuple(reader.turns)
