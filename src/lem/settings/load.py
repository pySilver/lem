"""The settings of a workspace, read from its main checkout: the team's file whole, and a
local file that may not hold a table of the team's (`settings/places.py`).

Read from the main checkout, never from a task's worktree, so that a branch cannot change the
checks or the base it is judged by. A slice of the step `settings`: the home file, the machine's
file and the seats come with it.
"""

import tomllib
from typing import TYPE_CHECKING

import msgspec

from lem.kernel.errors import Refusal
from lem.records.base import Frozen
from lem.settings import places
from lem.settings.team import Team

if TYPE_CHECKING:
    from pathlib import Path

INIT = "lem init --base BRANCH writes it"


class Shown(Frozen, frozen=True, kw_only=True):
    """What `lem settings show` prints: the settings, or None where Lem is not set up, and
    the file they come from."""

    settings: Team | None = None
    source: str | None = msgspec.field(default=None, name="from")


def tables(path: Path) -> dict[str, object]:
    """The tables of one TOML file; a file that is not TOML is refused with its line."""
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise Refusal(
            "settings-toml",
            f"{path} is not TOML: {error}",
            f"correct {path}, then run the command again",
        ) from error


def local_tables(checkout: Path) -> None:
    """Refuse a local file that holds a table only the team's file may."""
    path = checkout / places.LOCAL
    if not path.is_file():
        return
    found = [name for name in places.TEAM_ONLY if name in tables(path)]
    if found:
        raise Refusal(
            "table-place",
            f"{path} holds [{found[0]}], which only {places.TEAM} may hold",
            f"move [{found[0]}] into {places.TEAM}, in git, or remove it",
        )


def team_of(checkout: Path) -> Team:
    """The team's settings of the main checkout `checkout`."""
    path = checkout / places.TEAM
    if not path.is_file():
        raise Refusal("no-settings", f"{path} is not there", INIT)
    local_tables(checkout)
    try:
        return msgspec.convert(tables(path), Team)
    except msgspec.ValidationError as error:
        raise Refusal(
            "settings",
            f"{path}: {error}",
            "correct the line as docs/settings.md says, then run the command again",
        ) from error


def base_of(team: Team) -> str:
    """The base branch; refused when the settings name none."""
    if team.branch.base is None:
        raise Refusal(
            "no-base",
            f"{places.TEAM} names no branch.base, so a task has nothing to start from",
            f"write branch.base into {places.TEAM}",
        )
    return team.branch.base


def show(checkout: Path | None) -> Shown:
    """The settings as `lem settings show` prints them; None where Lem is not set up."""
    if checkout is None:
        return Shown()
    return Shown(settings=team_of(checkout), source=str(checkout / places.TEAM))
