"""`FakeHarness`: the `Harness` port over seats and transcripts a test sets, with every launch
recorded."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from lem.ports.harness import Missing, Seat, Signs, Tokens, Transcript

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class FakeHarness:
    """Seats that fail, transcripts by task, their signs and tokens, and the launches."""

    missing: dict[str, Missing] = field(default_factory=dict)
    by_task: dict[str, tuple[Transcript, ...]] = field(default_factory=dict)
    signs_of: dict[str, Signs] = field(default_factory=dict)
    tokens_of: dict[str, Tokens] = field(default_factory=dict)
    launches: list[tuple[Seat, str, Path, Path | None]] = field(default_factory=list)

    def launch(self, seat: Seat, brief: str, cwd: Path, plugin_dir: Path | None) -> str:
        self.launches.append((seat, brief, cwd, plugin_dir))
        return f"claude-{len(self.launches)}"

    def transcripts(self, task: str) -> tuple[Transcript, ...]:
        return self.by_task.get(task, ())

    def signs(self, transcript: Transcript) -> Signs:
        return self.signs_of.get(transcript.path, Signs())

    def tokens(self, transcripts: tuple[Transcript, ...]) -> Tokens:
        total = Tokens()
        for transcript in transcripts:
            one = self.tokens_of.get(transcript.path, Tokens(missing=1))
            total = Tokens(
                **{
                    name: getattr(total, name) + getattr(one, name)
                    for name in Tokens.__struct_fields__
                }
            )
        return total

    def available(self, seat: Seat) -> Missing | None:
        return self.missing.get(seat.agent)
