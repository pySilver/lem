"""Lem's settings for one checkout on this machine: the values in force, each with the file it
comes from (`reading.py` reads and checks the four files).

The team's file is the main checkout's: a task's worktree reads the same settings, so a branch
cannot change the checks, the base or the topics it is judged by. With no team's file Lem is
not set up there, and only the machine's and the developer's files are read.
"""

import os
from typing import TYPE_CHECKING

from lem.kernel import paths
from lem.kernel.errors import Refusal
from lem.records.base import Frozen
from lem.settings import base, effective, files, places, reading
from lem.settings.machine import Machine
from lem.settings.team import Team

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from lem.ports.git import GitFacts

type Environ = Mapping[str, str]

INIT = "lem init --base BRANCH writes it"


class Loaded(Frozen, frozen=True, kw_only=True):
    """The settings in force, each key's `from`, and the line that says the team's file is the
    base's commit, not the copy checked out in the main checkout."""

    settings: effective.Effective
    sources: dict[str, str]
    notice: str | None = None


def settings_of(
    checkout: Path | None, environ: Environ, git: GitFacts | None = None
) -> Loaded:
    """The settings in force for `checkout`, a main checkout where Lem is set up, or None
    outside one."""
    home = paths.home(environ)
    return loaded(reading.Where(checkout=checkout, home=home, environ=environ, git=git))


def loaded(where: reading.Where) -> Loaded:
    """The settings in force for the files of `where`, each checked."""
    named = reading.read(where)
    in_force = files.converted(
        effective.merged(named), effective.Effective, "the settings"
    )
    return Loaded(
        settings=in_force, sources=effective.sources(named), notice=notice_of(named)
    )


def notice_of(named: list[effective.Named]) -> str | None:
    """The line that says the team's file is the base's commit, or None."""
    said = (base.branch_of(name) for _, name in named)
    held = next((one for one in said if one), None)
    if held is None:
        return None
    return (
        f"the main checkout is not on {held}, so Lem reads {places.TEAM} as {held}'s "
        "newest commit has it, not the copy checked out there"
    )


def team_of(checkout: Path) -> Team:
    """The team's settings of the main checkout `checkout`; refused where Lem is not set up,
    and when the team's or the local file does not read."""
    path = checkout / places.TEAM
    if not path.is_file():
        raise Refusal("no-settings", f"{path} is not there", INIT)
    where = reading.Where(
        checkout=checkout, home=paths.home(os.environ), environ=os.environ
    )
    named = reading.read(where, places.REPOSITORY)
    team, name = named[0]
    return files.converted(team, Team, name)


def base_of(team: Team) -> str:
    """The base branch; refused when the settings name none."""
    if team.branch.base is None:
        raise Refusal(
            "no-base",
            f"{places.TEAM} names no branch.base, so a task has nothing to start from",
            f"write branch.base into {places.TEAM}",
        )
    return team.branch.base


def machine_of(environ: Mapping[str, str]) -> Machine:
    """This machine's file, checked; its defaults when it is not there."""
    where = reading.Where(checkout=None, home=paths.home(environ), environ=environ)
    tables, name = reading.read(where, (places.Scope.machine,))[0]
    return files.converted(tables, Machine, name)
