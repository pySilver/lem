"""The four files read, nearest first, each checked whole: its tables in their places, its
keys, its values, its seats, and the rules its types alone do not hold.

Each file is checked whole, the far ones too, so that a wrong line is refused wherever it is.
The team's file is the main checkout's (`base.py`); a repository's two files are read only in a
checkout where Lem is set up.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.settings import base, checked, files, places, seated
from lem.settings.machine import HANDOFF_FLOOR, Machine
from lem.settings.personal import Home, Local
from lem.settings.team import Team

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from lem.ports.git import GitFacts

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
    home folder, the environment that names it, the git that reads the base, and a file as an
    edit would leave it, which is checked with the others before the edit is written."""

    checkout: Path | None
    home: Path
    environ: Mapping[str, str]
    git: GitFacts | None = None
    # A file's tables as an edit would leave them, read in the place of the file on disk.
    edited: tuple[tuple[places.Scope, files.Tables], ...] = ()

    def named(self, scope: places.Scope) -> str:
        """The name of one of the four files, as a refusal and `from` give it."""
        return places.named(scope, self.home, self.environ)


def check(tables: files.Tables, scope: places.Scope, name: str, where: Where) -> None:
    """Refuse a table, a key or a value of one file that Lem cannot use."""
    files.placed(tables, scope, where.named)
    files.keyed(tables, dict(SHAPES)[scope], name)
    found = files.converted(tables, dict(SHAPES)[scope], name)
    seats = tables.get("seats")
    if isinstance(seats, dict):
        seated.seated(seats, name)
    if isinstance(found, Team) and where.checkout is not None:
        checked.paths(where.checkout, found.paths, name)
        checked.branch(found.branch, name)
    if isinstance(found, Machine):
        checked.handoff(found.handoff, name, HANDOFF_FLOOR)
        if found.serve.tailscale:
            checked.serve_ports(found.serve.port, found.serve.tailscale_port)


def source(scope: places.Scope, where: Where) -> Named:
    """The tables of one file, and its name; none when the file is not there."""
    if scope == places.Scope.team and where.checkout is not None:
        body, name = base.team_text(where.checkout, where.git)
        return files.decoded(body, name), name
    name = where.named(scope)
    edited = dict(where.edited).get(scope)
    if edited is not None:
        return edited, name
    path = places.path_of(scope, where.home)
    if scope == places.Scope.local and where.checkout is not None:
        path = where.checkout / path
    return files.read(path, name), name


def checked_source(scope: places.Scope, where: Where) -> Named:
    """One file read and checked."""
    tables, name = source(scope, where)
    check(tables, scope, name, where)
    return tables, name


def sourced(scope: places.Scope, where: Where) -> Named:
    """One file read and checked; a refusal of the base's committed file says where its fix
    counts."""
    try:
        return checked_source(scope, where)
    except Refusal as refused:
        held = base.branch_of(refused.why)
        if held is None:
            raise
        raise Refusal(
            refused.code, refused.why, counted(held, refused.fix)
        ) from refused


def counted(held: str, fix: str) -> str:
    """The fix of a line of the base `held`'s committed file."""
    counts = (
        f"Lem reads {base.OWN} as {held} has it, so a fix counts once it is committed"
    )
    return f"{counts} on {held}: {fix}"


def read(where: Where, wanted: places.Scopes = places.NEAREST) -> list[Named]:
    """The tables of each file of `wanted` that is there, nearest first, each checked, with
    its name; a repository's files only in a checkout."""
    found: list[Named] = []
    for scope in wanted:
        if where.checkout is None and scope in places.REPOSITORY:
            continue
        found.append(sourced(scope, where))
    return found
