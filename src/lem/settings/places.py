"""Where Lem's settings are: four files, the files where each table is valid
(`state.TABLE_PLACES` on `main`), and the name each file has in a message and in `from`.

What is true for the whole machine is in its file alone, and nothing overrides it; what guards
a team's repository is in the team's file alone, so that one developer's local file cannot lift
it; the question page's defaults are the developer's. A value that more than one file may hold
comes from the nearest file that holds it, in the order of NEAREST, else Lem's default.
"""

import enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping


class Scope(enum.StrEnum):
    """One of the four files: this machine's, the developer's for every repository, the
    team's, and the developer's for one repository."""

    machine = enum.auto()
    home = enum.auto()
    team = enum.auto()
    local = enum.auto()


type Scopes = tuple[Scope, ...]
type Valid = tuple[tuple[str, Scopes], ...]

LEM = Path(".lem")
TEAM = LEM / "settings.toml"
LOCAL = LEM / "settings.local.toml"
# The two files of Lem's home folder.
HOME = "settings.toml"
MACHINE = "machine.toml"
# Where a value no file names comes from.
DEFAULT = "Lem's default"
# The first file that holds a key gives its value.
NEAREST: Scopes = (Scope.local, Scope.team, Scope.home, Scope.machine)
# The order in which a refusal names the files where a table is valid.
ORDER: Scopes = tuple(Scope)
# The files of a repository, read only in one.
REPOSITORY: Scopes = (Scope.team, Scope.local)
MACHINE_ONLY: Scopes = (Scope.machine,)
TEAM_ONLY: Scopes = (Scope.team,)
# Each table, and the files where it is valid.
TABLES: Valid = (
    ("load", MACHINE_ONLY),
    ("serve", MACHINE_ONLY),
    ("peers", MACHINE_ONLY),
    ("handoff", MACHINE_ONLY),
    ("corrections", MACHINE_ONLY),
    ("seats", (Scope.home, *REPOSITORY)),
    ("ask", (Scope.home,)),
    ("flow", TEAM_ONLY),
    ("checks", TEAM_ONLY),
    ("branch", TEAM_ONLY),
    ("paths", TEAM_ONLY),
    ("tracker", TEAM_ONLY),
    ("jev", TEAM_ONLY),
    ("naps", REPOSITORY),
    ("state", REPOSITORY),
)
NAMES = tuple(table for table, _ in TABLES)


def valid(table: str) -> Scopes:
    """The files where `table` may stand; none for a table Lem does not know."""
    return next((scopes for name, scopes in TABLES if name == table), ())


def shown(path: Path, environ: Mapping[str, str]) -> str:
    """A file of the home directory as a person writes it, `~/.config/lem/settings.toml`;
    any other path as it is."""
    user = environ.get("HOME")
    if user and path.is_relative_to(user):
        relative = path.relative_to(user).as_posix()
        return f"~/{relative}"
    return str(path)


def path_of(scope: Scope, home: Path) -> Path:
    """The path of one file: a repository's relative to its checkout, the others in Lem's
    home folder `home`."""
    if scope in REPOSITORY:
        return TEAM if scope == Scope.team else LOCAL
    name = MACHINE if scope == Scope.machine else HOME
    return home / name


def named(scope: Scope, home: Path, environ: Mapping[str, str]) -> str:
    """The name of one of the four files, as a refusal and `from` give it."""
    return shown(path_of(scope, home), environ)
