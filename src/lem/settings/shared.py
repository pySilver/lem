"""The tables more than one file may hold, `[seats]`, `[naps]` and `[state]`, and the
developer's `[ask]` (docs/settings.md).

A seat is one string, `agent/model:effort` (the owner, 2026-11-17); `seats.py` reads its parts
and holds which seat must be written whole. Lem's own seat for each is "claude/opus:high" (the
owner, 2026-11-22 and 2026-11-23), and its experts are the newest Fable through Claude Code and
the newest Astra through Codex (2026-11-18). The days the state folder keeps are the owner's
thirty (2026-11-21).
"""

from typing import Annotated, Literal

import msgspec

from lem.settings.table import Table, Words

SEAT = "claude/opus:high"
EXPERTS = ("claude/fable:high", "codex/gpt-6.2-astra:high")
KEEP_DAYS = 30

type Experts = Annotated[tuple[Words, ...], msgspec.Meta(min_length=1, max_length=2)]
type Fallback = Words | Literal[False]
type Style = Literal["refined", "minimal", "bold", "terminal"]
type Review = Literal["auto", "always", "never"] | bool


class Seats(Table, frozen=True, kw_only=True):
    """`[seats]`: who sits where, each "agent/model:effort"."""

    reviewer: Annotated[
        Words,
        msgspec.Meta(
            description='seats.reviewer: a whole seat, as "codex/gpt-6.2-sol:high"'
        ),
    ] = SEAT
    planner: Annotated[
        Words,
        msgspec.Meta(description='seats.planner: a whole seat, as "claude/opus:high"'),
    ] = SEAT
    merger: Annotated[
        Words, msgspec.Meta(description='seats.merger: a seat, as "claude:high"')
    ] = SEAT
    session: Annotated[
        Words, msgspec.Meta(description='seats.session: a seat, as "claude:high"')
    ] = SEAT
    experts: Annotated[
        Experts,
        msgspec.Meta(
            description='seats.experts: one or two whole seats, as ["claude/fable:high"]'
        ),
    ] = EXPERTS
    fallback: Annotated[
        Fallback,
        msgspec.Meta(
            description='seats.fallback: a whole seat, as "claude/opus:high", or false'
        ),
    ] = SEAT


class Naps(Table, frozen=True, kw_only=True):
    """`[naps]`: whether Lem takes a nap now and then."""

    on: Annotated[bool, msgspec.Meta(description="naps.on: true or false")] = False


class State(Table, frozen=True, kw_only=True):
    """`[state]`: the days the state folder keeps what Lem no longer needs."""

    keep_days: Annotated[
        int,
        msgspec.Meta(
            ge=1, description="state.keep_days: a whole number of days, 1 or more"
        ),
    ] = KEEP_DAYS


class Ask(Table, frozen=True, kw_only=True):
    """`[ask]` of the home file: the question page's defaults."""

    style: Annotated[
        Style,
        msgspec.Meta(
            description='ask.style: "refined", "minimal", "bold" or "terminal"'
        ),
    ] = "refined"
    size: Annotated[
        Words | int,
        msgspec.Meta(description='ask.size: a percent of the pane, "auto" or "full"'),
    ] = "auto"
    review: Annotated[
        Review,
        msgspec.Meta(
            description='ask.review: "auto", "always", "never", true or false'
        ),
    ] = "auto"
    browser: Annotated[bool, msgspec.Meta(description="ask.browser: true or false")] = (
        False
    )
    status: Annotated[
        dict[Literal["asking", "answered"], tuple[Words, ...]],
        msgspec.Meta(
            description='ask.status: {asking = ["blocked"], answered = ["active"]}'
        ),
    ] = msgspec.field(
        default_factory=lambda: {"asking": ("blocked",), "answered": ("active",)}
    )
