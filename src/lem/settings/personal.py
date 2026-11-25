"""The developer's two files: `.lem/settings.local.toml`, his for one repository on this
machine, and `settings.toml` of Lem's home folder, his for every repository.

The local file may say no to the naps and nothing else about them: a nap spends this person's
tokens, and only the team's file, which everybody reads in git, turns them on. It may set its own
days for the state folder, lower or higher than the team's: one developer's disk is not
another's (the owner, 2026-11-21).
"""

from typing import Annotated, Literal

import msgspec

from lem.settings.shared import Ask, Seats
from lem.settings.table import Table


class LocalNaps(Table, frozen=True, kw_only=True):
    """`[naps]` of the local file: only `on = false`."""

    on: Annotated[
        Literal[False] | None,
        msgspec.Meta(
            description="naps.on: only false here; .lem/settings.toml turns the naps on"
        ),
    ] = None


class LocalState(Table, frozen=True, kw_only=True):
    """`[state]` of the local file: this machine's own days."""

    keep_days: Annotated[
        int | None,
        msgspec.Meta(
            ge=1, description="state.keep_days: a whole number of days, 1 or more"
        ),
    ] = None


class Local(Table, frozen=True, kw_only=True):
    """`.lem/settings.local.toml` whole."""

    seats: Seats = Seats()
    naps: LocalNaps = LocalNaps()
    state: LocalState = LocalState()


class Home(Table, frozen=True, kw_only=True):
    """`settings.toml` of Lem's home folder whole."""

    seats: Seats = Seats()
    ask: Ask = Ask()
