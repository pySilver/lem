"""The tokens a task's Claude Code transcripts spent, for the `Harness` port on Claude Code
(`harness_claude`).

An `assistant` record carries the reply's `message.usage`, and Claude Code writes one record for
each block of a reply, each with the same `message.id` and the same `usage`, so a reply counts
once by its id, else by the record's `uuid` (read on 2026-11-21 in one transcript of Claude Code
2.1.327: 166 assistant records of 58 replies, the usage of one id the same in all its records:
`tokens.py` on `main`). A session's subagents keep theirs beside it, in
`ID/subagents/agent-*.jsonl`; they count too. The four sums are `input_tokens`,
`output_tokens`, `cache_read_input_tokens` and `cache_creation_input_tokens`. A transcript that
is gone or does not read counts in `missing`, a line that is no JSON in `unread`.

It counts only what Claude Code wrote on this machine: a Codex reviewer, an expert of another
provider and a session of the task on another machine are not in it.
"""

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import msgspec

from lem.ports.harness import Tokens

if TYPE_CHECKING:
    from collections.abc import Iterable

    from lem.ports.harness import Transcript


class Usage(msgspec.Struct, frozen=True, kw_only=True):
    """What one reply spent."""

    input_tokens: int | None = None
    output_tokens: int | None = None
    cache_read_input_tokens: int | None = None
    cache_creation_input_tokens: int | None = None


class Said(msgspec.Struct, frozen=True, kw_only=True):
    """A record's message: the reply's id and what it spent."""

    reply: str | None = msgspec.field(default=None, name="id")
    usage: Usage | None = None


class Record(msgspec.Struct, frozen=True, kw_only=True):
    """A record of a transcript, by the keys the tokens read."""

    kind: str = msgspec.field(default="", name="type")
    uuid: str | None = None
    message: Said | None = None


@dataclass
class Tally:
    """The sums and counts of a task's transcripts so far, and the replies already counted."""

    counts: Counter[str] = field(default_factory=Counter)
    seen: set[str] = field(default_factory=set)

    def add_transcript(self, path: Path) -> None:
        """Add a session's transcript and its subagents'."""
        if not self.add_file(path):
            self.counts["missing"] += 1
            return
        self.counts["sessions"] += 1
        folder = path.with_suffix("") / "subagents"
        for agent in sorted(folder.glob("agent-*.jsonl")):
            if self.add_file(agent):
                self.counts["subagents"] += 1

    def add_file(self, path: Path) -> bool:
        """Add each reply of the file at `path`; False when it does not read."""
        try:
            with path.open("rb") as lines:
                self.add_lines(lines)
        except OSError:
            return False
        return True

    def add_lines(self, lines: Iterable[bytes]) -> None:
        """Add the reply of each line that holds one; a line that is no JSON is unread."""
        for line in lines:
            if line.strip():
                self.add_line(line)

    def add_line(self, line: bytes) -> None:
        """Add the reply of one line; a line that is JSON of another form holds none."""
        try:
            record = msgspec.json.decode(line, type=Record)
        except msgspec.ValidationError:
            return
        except msgspec.DecodeError:
            self.counts["unread"] += 1
            return
        self.add_reply(record)

    def add_reply(self, record: Record) -> None:
        """Add what a reply spent, once by its id."""
        said = record.message
        if record.kind != "assistant" or said is None or said.usage is None:
            return
        key = said.reply or record.uuid
        if key is not None:
            if key in self.seen:
                return
            self.seen.add(key)
        usage = said.usage
        self.counts.update(
            input=usage.input_tokens or 0,
            output=usage.output_tokens or 0,
            cache_read=usage.cache_read_input_tokens or 0,
            cache_write=usage.cache_creation_input_tokens or 0,
        )


def tokens_of(transcripts: tuple[Transcript, ...]) -> Tokens:
    """The tokens of `transcripts` and their subagents, each reply once."""
    tally = Tally()
    for transcript in transcripts:
        tally.add_transcript(Path(transcript.path))
    return Tokens(**tally.counts)
