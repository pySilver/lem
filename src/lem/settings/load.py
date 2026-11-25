"""Lem's settings for one checkout on this machine: the four files read, each checked whole,
and the values in force with the file each comes from.

The team's file is the main checkout's (`base.py`): a task's worktree reads the same settings,
so a branch cannot change the checks, the base or the topics it is judged by. Each file is
checked whole, the far ones too, so that a wrong line is refused wherever it is. With no team's
file Lem is not set up there, and only the machine's and the developer's files are read.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from lem.kernel import paths
from lem.kernel.errors import Refusal
from lem.records.base import Frozen
from lem.settings import base, checked, effective, files, places
from lem.settings.machine import HANDOFF_FLOOR, Machine
from lem.settings.personal import Home, Local
from lem.settings.team import Team

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from lem.ports.git import GitPlaces

INIT = "lem init --base BRANCH writes it"
# The files of a repository, read only in one.
REPOSITORY = frozenset(("team", "local"))
SHAPES = (("machine", Machine), ("home", Home), ("team", Team), ("local", Local))


class Loaded(Frozen, frozen=True, kw_only=True):
    """The settings in force, each key's `from`, and whether the team's file is there."""

    settings: effective.Effective
    sources: dict[str, str]
    onboarded: bool


def shape_of(file: places.File) -> type[Machine | Home | Team | Local]:
    """The struct of one of the four files."""
    return next(shape for name, shape in SHAPES if name == file)


@dataclass(frozen=True, kw_only=True, slots=True)
class Where:
    """Where the four files are: the main checkout (None outside a set-up repository), Lem's
    home folder, the environment that names it, and the git that reads the base."""

    checkout: Path | None
    home: Path
    environ: Mapping[str, str]
    git: GitPlaces | None = None

    def named(self, file: places.File) -> str:
        """The name of one of the four files, as a refusal and `from` give it."""
        return places.named(file, self.home, self.environ)

    def path(self, file: places.File) -> Path:
        """The path of the local, home or machine file."""
        if file == "local" and self.checkout is not None:
            return self.checkout / places.LOCAL
        return self.home / (places.MACHINE if file == "machine" else places.HOME)


def check(tables: files.Tables, file: places.File, name: str, where: Where) -> None:
    """Refuse a table, a key or a value of one file that Lem cannot use."""
    shape = shape_of(file)
    files.placed(tables, file, lambda one: name if one == file else where.named(one))
    files.keyed(tables, shape, name)
    found = files.converted(tables, shape, name)
    seated = tables.get("seats")
    if isinstance(seated, dict):
        checked.seated(seated, name)
    if isinstance(found, Team) and where.checkout is not None:
        checked.paths(where.checkout, found.paths, name)
        checked.branch(found.branch, name)
    if isinstance(found, Machine):
        checked.handoff(found.handoff, name, HANDOFF_FLOOR)


def source(file: places.File, where: Where) -> effective.Named:
    """The tables of one file, and its name; none when the file is not there."""
    if file == "team" and where.checkout is not None:
        body, name = base.team_text(where.checkout, where.git)
        return files.decoded(body, name), name
    name = where.named(file)
    return files.read(where.path(file), name), name


def read(
    where: Where, wanted: tuple[places.File, ...] = places.NEAREST
) -> list[effective.Named]:
    """The tables of each file of `wanted` that is there, nearest first, each checked, with
    its name; a repository's files only in a checkout."""
    found: list[effective.Named] = []
    for file in wanted:
        if where.checkout is None and file in REPOSITORY:
            continue
        tables, name = source(file, where)
        check(tables, file, name, where)
        found.append((tables, name))
    return found


def settings_of(
    checkout: Path | None, environ: Mapping[str, str], git: GitPlaces | None = None
) -> Loaded:
    """The settings in force for `checkout` (None outside a set-up repository)."""
    where = Where(checkout=checkout, home=paths.home(environ), environ=environ, git=git)
    named = read(where)
    onboarded = checkout is not None and (checkout / places.TEAM).is_file()
    in_force = files.converted(
        effective.merged(named), effective.Effective, "the settings"
    )
    return Loaded(
        settings=in_force, sources=effective.sources(named), onboarded=onboarded
    )


def team_of(checkout: Path) -> Team:
    """The team's settings of the main checkout `checkout`; refused where Lem is not set up,
    and when the team's or the local file does not read."""
    if not (checkout / places.TEAM).is_file():
        raise Refusal("no-settings", f"{checkout / places.TEAM} is not there", INIT)
    where = Where(checkout=checkout, home=checkout, environ={})
    _, (team, name) = read(where, ("local", "team"))
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
    where = Where(checkout=None, home=paths.home(environ), environ=environ)
    ((tables, name),) = read(where, ("machine",))
    return files.converted(tables, Machine, name)
