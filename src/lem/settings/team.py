"""The team's file, `.lem/settings.toml` in git: the tables that guard a change, and the
team's seats (docs/settings.md).

Each table is a frozen struct that refuses a key it does not know, and each field's
description is the fix a refusal of its value names. The values that a nearer file may hold
(`[seats]`, `[naps]`, `[state]`) are `shared.py`'s.
"""

from typing import Annotated, Literal

import msgspec

from lem.settings.shared import Naps, Seats, State
from lem.settings.table import Lines, Table, Words

type Land = Literal["agent", "owner"]
type History = Literal["squash", "keep"]
type Kind = Literal["linear", "github"]


class Paths(Table, frozen=True, kw_only=True):
    """`[paths]`: the folder of the plans, the name of a plan's file, and the rulings file,
    each relative to the root of the checkout."""

    plans: Annotated[
        Words,
        msgspec.Meta(description='paths.plans: a folder, as plans = "docs/plans"'),
    ] = "docs/plans"
    plan_file: Annotated[
        Words,
        msgspec.Meta(
            description='paths.plan_file: a file name, as plan_file = "YYYY-MM-DD-<slug>.md"'
        ),
    ] = "YYYY-MM-DD-<slug>.md"
    rulings: Annotated[
        Words,
        msgspec.Meta(
            description='paths.rulings: a markdown file, as rulings = "docs/rulings.md"'
        ),
    ] = "docs/rulings.md"


class Branch(Table, frozen=True, kw_only=True):
    """`[branch]`: the base a task starts from and lands on, who merges, what lands, and the
    branches Lem never touches."""

    base: Annotated[
        Words | None,
        msgspec.Meta(
            description='branch.base: the branch a task starts from and lands on, as base = "main"'
        ),
    ] = None
    land: Annotated[
        Land, msgspec.Meta(description='branch.land: "agent" or "owner", who merges')
    ] = "agent"
    history: Annotated[
        History, msgspec.Meta(description='branch.history: "squash" or "keep"')
    ] = "squash"
    protected: Annotated[
        Lines,
        msgspec.Meta(description="branch.protected: the branches Lem lands nothing on"),
    ] = ()


class Checks(Table, frozen=True, kw_only=True):
    """`[checks]`: the whole suite, the tests two tasks cannot run at once, and what a new
    worktree needs before its tests run."""

    commands: Annotated[
        Lines,
        msgspec.Meta(
            description="checks.commands: the whole suite, a list of commands"
        ),
    ] = ()
    serial: Annotated[
        Lines,
        msgspec.Meta(
            description="checks.serial: the tests two tasks cannot run at once, a list"
        ),
    ] = ()
    setup: Annotated[
        Lines,
        msgspec.Meta(
            description="checks.setup: what a new worktree needs first, a list"
        ),
    ] = ()


class Flow(Table, frozen=True, kw_only=True):
    """`[flow]`: what must never go wrong, as sentences in the owner's words."""

    topics: Annotated[
        Lines,
        msgspec.Meta(
            description="flow.topics: a list of sentences in the owner's words"
        ),
    ] = ()


class Tracker(Table, frozen=True, kw_only=True):
    """`[tracker]`: where a task's ask may come from; the table is left out with none."""

    kind: Annotated[
        Kind,
        msgspec.Meta(
            description='tracker.kind: "linear" or "github"; leave [tracker] out with none'
        ),
    ]


class Jev(Table, frozen=True, kw_only=True):
    """`[jev]`: whether the landing sends a finding to the Jev model."""

    findings: Annotated[
        bool, msgspec.Meta(description="jev.findings: true or false")
    ] = True


class Team(Table, frozen=True, kw_only=True):
    """The team's file whole."""

    paths: Paths = Paths()
    branch: Branch = Branch()
    checks: Checks = Checks()
    flow: Flow = Flow()
    seats: Seats = Seats()
    tracker: Tracker | None = None
    naps: Naps = Naps()
    state: State = State()
    jev: Jev = Jev()
