"""The brief, the seats assigned to it, and the answers on record."""

from lem.records.base import Frozen, Moment
from lem.settings.seats import Seat


class Named(Seat, frozen=True, kw_only=True):
    """The expert's seat and the name the answer carries."""

    name: str
    place: str | None


class Assigned(Named, frozen=True, kw_only=True, omit_defaults=False):
    """The expert's seat and its own answer file."""

    answer: str


class Answer(Frozen, frozen=True, kw_only=True):
    """An expert's words, with either an answer, a pick or no fit."""

    why: str
    at: Moment
    pick: str | None = None
    answer: str | None = None
    none: bool = False


class Asked(Frozen, frozen=True, kw_only=True):
    """What the owner or the lead asks the experts."""

    question: str
    context: str = ""
    options: tuple[str, ...] = ()
    files: tuple[str, ...] = ()
    seats: tuple[str, ...] = ()


class Record(Frozen, frozen=True, kw_only=True):
    """The brief and its record of answers, written whole."""

    question: str
    context: str
    options: tuple[str, ...]
    files: tuple[str, ...]
    asked: Moment
    checkout: str
    experts: tuple[Assigned, ...]
    answers: dict[str, Answer]


class Brief(Frozen, frozen=True, kw_only=True):
    """The paths and seats the harness takes from the brief command."""

    folder: str
    dir: str
    brief: str
    worktree: str
    experts: tuple[Assigned, ...]
    answers: dict[str, str]
    ask: tuple[str, ...]


class Summary(Record, frozen=True, kw_only=True):
    """The record, with an agreement and the answers that still wait."""

    folder: str
    dir: str
    agree: str | None
    waiting: tuple[str, ...]
