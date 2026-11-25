"""The team's settings that the fast track reads: `[branch]` and `[checks]` of
`.lem/settings.toml` (docs/settings.md).

A slice of the step `settings`, which adds every other table. Each table refuses a key it does not
know, and each field's description is the fix a refusal names. The other tables of the file are
read past until that step gives them a struct.
"""

from typing import Annotated, Literal

import msgspec

type Land = Literal["agent", "owner"]
type History = Literal["squash", "keep"]
type Commands = tuple[str, ...]


class Branch(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """`[branch]`: the base a task starts from and lands on, who merges, what lands, and the
    branches Lem never touches."""

    base: Annotated[
        str | None,
        msgspec.Meta(
            description="branch.base: the branch a task starts from and lands on"
        ),
    ] = None
    land: Annotated[
        Land, msgspec.Meta(description='branch.land: "agent" or "owner", who merges')
    ] = "agent"
    history: Annotated[
        History, msgspec.Meta(description='branch.history: "squash" or "keep"')
    ] = "squash"
    protected: Annotated[
        Commands,
        msgspec.Meta(description="branch.protected: the branches Lem lands nothing on"),
    ] = ()


class Checks(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """`[checks]`: the whole suite, the tests two tasks cannot run at once, and what a new
    worktree needs before its tests run."""

    commands: Annotated[
        Commands, msgspec.Meta(description="checks.commands: the whole suite, a list")
    ] = ()
    serial: Annotated[
        Commands,
        msgspec.Meta(
            description="checks.serial: the tests two tasks cannot run at once"
        ),
    ] = ()
    setup: Annotated[
        Commands,
        msgspec.Meta(description="checks.setup: what a new worktree needs first"),
    ] = ()


class Team(msgspec.Struct, frozen=True, kw_only=True):
    """The tables of the team's file that this slice reads."""

    branch: Branch = Branch()
    checks: Checks = Checks()
