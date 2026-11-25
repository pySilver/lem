"""The `Harness` port: the coding agent that runs a seat, and what its transcripts say (the
design's part 4).

A transcript counts for a task by the rule of part 3: read across every task's sessions file and
summary, each path once, by its first prompt, and by the recorded task when the prompt names
none.
"""

from typing import TYPE_CHECKING, Literal, Protocol

from lem.records.base import Frozen, Moment, Slug

if TYPE_CHECKING:
    from pathlib import Path


class Seat(Frozen, frozen=True, kw_only=True):
    """An agent, its model and its effort, as `agent/model:effort` names it."""

    agent: str
    model: str | None = None
    effort: str | None = None


class Missing(Frozen, frozen=True, kw_only=True):
    """A seat that cannot run here: the kind of error, and what the agent said."""

    error: Literal["missing", "login", "tokens", "model"]
    said: str | None = None


class Transcript(Frozen, frozen=True, kw_only=True):
    """A transcript of a task's session: its path and session id."""

    path: str
    claude: str


class Signs(Frozen, frozen=True, kw_only=True):
    """The signs of work of a session: its newest sign, a shell command that runs, whether a
    turn runs or ended, and whether its process could be read. The newest sign comes from the
    transcript and can be known with `read=False`."""

    sign: Moment | None = None
    shell: bool = False
    turn: Literal["runs", "ended"] | None = None
    read: bool = True


class Tokens(Frozen, frozen=True, kw_only=True):
    """The tokens a task's transcripts spent, and what could not be read."""

    input: int = 0
    output: int = 0
    cache_read: int = 0
    cache_write: int = 0
    sessions: int = 0
    subagents: int = 0
    missing: int = 0
    unread: int = 0


class Harness(Protocol):
    """Launch a seat, and read its transcripts."""

    def launch(
        self, seat: Seat, brief: str, cwd: Path, plugin_dir: Path | None
    ) -> str: ...
    def transcripts(self, task: Slug) -> tuple[Transcript, ...]: ...
    def signs(self, transcript: Transcript) -> Signs: ...
    def tokens(self, transcripts: tuple[Transcript, ...]) -> Tokens: ...
    def available(self, seat: Seat) -> Missing | None: ...
