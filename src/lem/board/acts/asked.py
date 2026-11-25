"""An act as the owner asked it, and its note when it was refused.

An act is a use case of `board/acts/` that takes `Asked` and gives a `Note`: it calls the same
`app` functions a command calls, and a refusal is its note, never an error page.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from lem.board.acts.notes import Note
from lem.store import places

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path

    from lem.board.acts.asker import Asker
    from lem.board.acts.given import Given
    from lem.kernel.errors import Refusal


@dataclass(frozen=True, kw_only=True, slots=True)
class Asked:
    """An act as the owner asked it: the workspace's main checkout, the task, the form, where
    it came from, and when."""

    checkout: Path
    slug: str
    given: Given
    asker: Asker
    now: datetime

    @property
    def state(self) -> Path:
        """The workspace's state folder."""
        return self.checkout / places.STATE


def line_of(refusal: Refusal) -> str:
    """A refusal as one line of a note: its why, and the fix when the why does not end it."""
    why = refusal.why
    if why.endswith("."):
        return why
    first = why[:1].upper()
    rest = why[1:]
    return f"{first}{rest}: {refusal.fix}."


def refused(act: str, slug: str | None, refusal: Refusal) -> Note:
    """The note of an act that was refused."""
    return Note(task=slug, act=act, state="refused", said=line_of(refusal))
