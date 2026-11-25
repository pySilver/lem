"""The four files read, nearest first, each checked whole: its tables in their places, its
keys, its values, its seats, and the rules its types alone do not hold.

Each file is checked whole, the far ones too, so that a wrong line is refused wherever it is.
The team's file is the main checkout's (`base.py`); a repository's two files are read only in a
checkout where Lem is set up.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from lem.settings import base, checked, files, places, seated
from lem.settings.machine import HANDOFF_FLOOR, Machine
from lem.settings.personal import Home, Local
from lem.settings.team import Team

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from lem.ports.git import GitPlaces

type Named = tuple[files.Tables, str]
type Shape = type[Machine | Home | Team | Local]
SHAPES: tuple[tuple[places.Scope, Shape], ...] = (
    (places.Scope.machine, Machine),
    (places.Scope.home, Home),
    (places.Scope.team, Team),
    (places.Scope.local, Local),
)


@dataclass(frozen=True, kw_only=True, slots=True)
class Where:
    """Where the four files are: the main checkout (None outside a set-up repository), Lem's
    home folder, the environment that names it, and the git that reads the base."""

    checkout: Path | None
    home: Path
    environ: Mapping[str, str]
    git: GitPlaces | None = None

    def named(self, scope: places.Scope) -> str:
        """The name of one of the four files, as a refusal and `from` give it."""
        return places.named(scope, self.home, self.environ)


def shape_of(scope: places.Scope) -> Shape:
    """The struct of one of the four files."""
    return next(shape for name, shape in SHAPES if name == scope)


def check(tables: files.Tables, scope: places.Scope, name: str, where: Where) -> None:
    """Refuse a table, a key or a value of one file that Lem cannot use."""
    files.placed(tables, scope, where.named)
    files.keyed(tables, shape_of(scope), name)
    found = files.converted(tables, shape_of(scope), name)
    seats = tables.get("seats")
    if isinstance(seats, dict):
        seated.seated(seats, name)
    if isinstance(found, Team) and where.checkout is not None:
        checked.paths(where.checkout, found.paths, name)
        checked.branch(found.branch, name)
    if isinstance(found, Machine):
        checked.handoff(found.handoff, name, HANDOFF_FLOOR)


def source(scope: places.Scope, where: Where) -> Named:
    """The tables of one file, and its name; none when the file is not there."""
    if scope == places.Scope.team and where.checkout is not None:
        body, name = base.team_text(where.checkout, where.git)
        return files.decoded(body, name), name
    path = places.path_of(scope, where.home)
    if scope == places.Scope.local and where.checkout is not None:
        path = where.checkout / path
    name = where.named(scope)
    return files.read(path, name), name


def read(where: Where, wanted: places.Scopes = places.NEAREST) -> list[Named]:
    """The tables of each file of `wanted` that is there, nearest first, each checked, with
    its name; a repository's files only in a checkout."""
    found: list[Named] = []
    for scope in wanted:
        if where.checkout is None and scope in places.REPOSITORY:
            continue
        tables, name = source(scope, where)
        check(tables, scope, name, where)
        found.append((tables, name))
    return found
