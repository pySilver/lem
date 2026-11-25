"""`SigningHarness`: the core's `FakeHarness` with the main-thread sign a task's session reads
beside the port (`app/sessions/beside.py`), set by transcript path."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from fakes.harness import FakeHarness

if TYPE_CHECKING:
    from datetime import datetime

    from lem.ports.harness import Transcript


@dataclass
class SigningHarness(FakeHarness):
    """Seats, transcripts, signs and tokens, and each transcript's main-thread sign; with
    none set, the transcript's own sign."""

    mains: dict[str, datetime] = field(default_factory=dict)

    def main_sign(self, transcript: Transcript) -> datetime | None:
        found = self.mains.get(transcript.path)
        return found if found is not None else self.signs(transcript).sign
