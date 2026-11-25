"""The criteria as approved, and the personas' read of them (`criteria.py` on `main`)."""

from typing import Literal

from lem.records.base import Frozen, Moment
from lem.records.criterion import Criterion

type Size = Literal["full", "small"]
# owner: his yes; lem: the fast track in his name; read: the lead after a clean persona read;
# alone: the owner away, or a night task.
type ApprovedBy = Literal["owner", "lem", "read", "alone"]


class Approval(Frozen, frozen=True, kw_only=True):
    """One approval: its number, who gave it, the size and its reason, the criteria it approved
    and their digest (their sentences and steps, `state.whole` on `main`), and the approval it
    replaces."""

    number: int
    at: Moment
    by: ApprovedBy
    size: Size
    why: str
    digest: str
    criteria: tuple[Criterion, ...]
    how: str | None = None
    replaces: int | None = None


class Silent(Frozen, frozen=True, kw_only=True):
    """A persona that gave no answer, `PERSONA, FAMILY`, and why."""

    name: str
    why: str


class PersonaRead(Frozen, frozen=True, kw_only=True):
    """One read of the criteria by the personas: who ran it, how many were asked and answered,
    the families that answered, the silent, the criteria read, flagged and split. A read with
    no answer, a flag or a split keeps the criteria for the owner."""

    by: Literal["lem", "lead"]
    started: Moment
    ended: Moment | None = None
    asked: int = 0
    answered: int = 0
    families: tuple[str, ...] = ()
    silent: tuple[Silent, ...] = ()
    criteria: int = 0
    flagged: int = 0
    split: bool = False
    digest: str | None = None
