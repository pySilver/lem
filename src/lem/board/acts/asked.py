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
    """A refusal's reason and its distinct recovery instruction."""
    why = refusal.why
    fix = refusal.fix.rstrip(".")
    if why.casefold().endswith(f"{fix.casefold()}."):
        return why
    if why.endswith((".", "?", "!")):
        sentence = fix[:1].upper() + fix[1:]
        return f"{why} {sentence}."
    first = why[:1].upper()
    rest = why[1:]
    return f"{first}{rest}: {fix}."


def refused(act: str, slug: str | None, refusal: Refusal) -> Note:
    """The note of an act that was refused."""
    return Note(task=slug, act=act, state="refused", said=line_of(refusal))
