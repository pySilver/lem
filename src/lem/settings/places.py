"""Where Lem's settings are: four files, the files where each table is valid
(`state.TABLE_PLACES` on `main`), and the name each file has in a message and in `from`.

What is true for the whole machine is in its file alone, and nothing overrides it; what guards
a team's repository is in the team's file alone, so that one developer's local file cannot lift
it; the question page's defaults are the developer's. A value that more than one file may hold
comes from the nearest file that holds it, in the order of NEAREST, else Lem's default.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from collections.abc import Mapping

type File = Literal["machine", "home", "team", "local"]

LEM = Path(".lem")
TEAM = LEM / "settings.toml"
LOCAL = LEM / "settings.local.toml"
# The two files of Lem's home folder.
HOME = "settings.toml"
MACHINE = "machine.toml"
# Where a value no file names comes from.
DEFAULT = "Lem's default"
# The first file that holds a key gives its value.
NEAREST: tuple[File, ...] = ("local", "team", "home", "machine")
# The order in which a refusal names the files where a table is valid.
ORDER: tuple[File, ...] = ("machine", "home", "team", "local")
# Each table, and the files where it is valid.
TABLES: tuple[tuple[str, tuple[File, ...]], ...] = (
    ("load", ("machine",)),
    ("serve", ("machine",)),
    ("peers", ("machine",)),
    ("handoff", ("machine",)),
    ("corrections", ("machine",)),
    ("seats", ("home", "team", "local")),
    ("ask", ("home",)),
    ("flow", ("team",)),
    ("checks", ("team",)),
    ("branch", ("team",)),
    ("paths", ("team",)),
    ("tracker", ("team",)),
    ("jev", ("team",)),
    ("naps", ("team", "local")),
    ("state", ("team", "local")),
)
NAMES = tuple(table for table, _ in TABLES)
# The tables valid in the team's file only: what guards the project.
TEAM_ONLY = tuple(table for table, files in TABLES if files == ("team",))


def valid(table: str) -> tuple[File, ...]:
    """The files where `table` may stand; none for a table Lem does not know."""
    return next((files for name, files in TABLES if name == table), ())


def shown(path: Path, environ: Mapping[str, str]) -> str:
    """A file of the home directory as a person writes it, `~/.config/lem/settings.toml`;
    any other path as it is."""
    user = environ.get("HOME")
    if user and path.is_relative_to(user):
        return f"~/{path.relative_to(user).as_posix()}"
    return str(path)


def named(file: File, home: Path, environ: Mapping[str, str]) -> str:
    """The name of one of the four files, as a refusal and `from` give it; `home` is Lem's
    home folder."""
    if file == "team":
        return TEAM.as_posix()
    if file == "local":
        return LOCAL.as_posix()
    return shown(home / (MACHINE if file == "machine" else HOME), environ)
