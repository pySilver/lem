"""A task's landing: its round, its phase, and the evidence each step left (`landing.md` A and
B). The due step is derived from this evidence and the world gathered now (`landing.md` C)."""

from typing import Literal

from lem.records.base import Frozen, Sha
from lem.records.landing.checks import Checked
from lem.records.landing.merge import (
    Cleaned,
    MergeAccepted,
    Merged,
    MergeIntent,
    Refused,
)
from lem.records.landing.propose import MergeRead, Proposed, Standing
from lem.records.landing.review import Filed, Reviewed
from lem.records.landing.start import Based, Polished, Resolution, Started

type Phase = Literal["preparing", "open", "merged", "ended"]


class Pull(Frozen, frozen=True, kw_only=True):
    """The pull request: its number, address and title."""

    number: int
    url: str
    title: str


class Landing(Frozen, frozen=True, kw_only=True):
    """The landing of one task. `pushed` is the head Lem pushed last, kept before the forge
    call; `reviews` and `reads` keep every attempt and read of the round; `archived` keeps the
    reviews of a landing that started over."""

    round: int = 1
    relands: int = 0
    phase: Phase = "preparing"
    pull: Pull | None = None
    pushed: Sha | None = None
    started: Started | None = None
    based: Based | None = None
    polished: Polished | None = None
    checked: Checked | None = None
    reviews: tuple[Reviewed, ...] = ()
    filed: tuple[Filed, ...] = ()
    resolution: Resolution | None = None
    proposed: Proposed | None = None
    reads: tuple[MergeRead, ...] = ()
    standing: Standing | None = None
    refused: Refused | None = None
    intent: MergeIntent | None = None
    accepted: MergeAccepted | None = None
    merged: Merged | None = None
    cleaned: Cleaned | None = None
    archived: tuple[Reviewed, ...] = ()
