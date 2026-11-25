"""The page's card metadata and the wire form of the owner's answer."""

from typing import Literal

import msgspec

from lem.records.base import Frozen

type Mode = Literal["single", "multi", "text", "tune"]
type End = Literal["answered", "dismissed", "closed"]


class Option(Frozen, frozen=True, kw_only=True):
    """An option as the card showed it."""

    id: str
    label: str


class Prompt(Frozen, frozen=True, kw_only=True):
    """One question on the page, with its options and mode."""

    id: str
    prompt: str
    mode: Mode
    options: tuple[Option, ...]
    optional: bool = False
    minimum: int = 0
    maximum: int | None = None


class Card(Frozen, frozen=True, kw_only=True):
    """The session that shows the card and what it asks."""

    page: str
    session: str
    prompts: tuple[Prompt, ...]


class Pick(Frozen, frozen=True, kw_only=True):
    """One component of the card's answer."""

    selected: tuple[str, ...] = ()
    labels: tuple[str, ...] = ()
    text: str | None = None
    controls: dict[str, object] | None = msgspec.field(name="values", default=None)
    preset: str | None = msgspec.field(name="from", default=None)
    extra: object = None


class Posted(Frozen, frozen=True, kw_only=True):
    """The JSON object the board's question page sends."""

    status: Literal["answered", "dismissed", "chat"]
    answers: dict[str, Pick] = msgspec.field(default_factory=dict)
    digest: str | None = None
