"""A backlog item's head, as its front matter and first heading hold it (`project.item_front`
on `main`). An open task that started from an item claims it."""

from typing import Literal

from lem.records.base import Day, Frozen


class ItemHead(Frozen, frozen=True, kw_only=True):
    """An item's worth, where it is, the day it was added, the proposals it came from, its
    title, and the reason it was decided against, if it was."""

    worth: Literal["later", "no"]
    where: str | None = None
    added: Day | None = None
    proposals: tuple[str, ...] = ()
    title: str
    decided_against: str | None = None
