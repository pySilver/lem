"""The settings in force: each key from the nearest file that holds it, else Lem's default,
with the name of that file as the key's `from`.

The four files are read nearest first (`places.NEAREST`), so a key of the local file wins over
the team's, the team's over the developer's home file, and a table only one file may hold comes
from that file. A list (`seats.experts`) is one value and is replaced whole.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.settings import places
from lem.settings.machine import Corrections, Handoff, Host, Load, Port, Serve
from lem.settings.shared import Ask, Naps, Seats, State
from lem.settings.table import Table
from lem.settings.team import Branch, Checks, Flow, Jev, Paths, Tracker

if TYPE_CHECKING:
    from collections.abc import Sequence

type Tables = dict[str, object]
type Named = tuple[Tables, str]


class Effective(Table, frozen=True, kw_only=True):
    """Every table, as it is in force for one checkout on this machine."""

    paths: Paths = Paths()
    branch: Branch = Branch()
    checks: Checks = Checks()
    flow: Flow = Flow()
    seats: Seats = Seats()
    tracker: Tracker | None = None
    naps: Naps = Naps()
    state: State = State()
    jev: Jev = Jev()
    ask: Ask = Ask()
    load: Load = Load()
    serve: Serve = Serve()
    peers: dict[Host, Port] = msgspec.field(default_factory=dict)
    handoff: Handoff = Handoff()
    corrections: Corrections = Corrections()


def merged(files: Sequence[Named]) -> Tables:
    """The tables of `files`, nearest first, each key from the first file that holds it."""
    found: dict[str, dict[str, object]] = {}
    for tables, _ in reversed(files):
        for table, body in tables.items():
            if isinstance(body, dict):
                found.setdefault(table, {}).update(body)
    return dict(found)


def keys() -> tuple[str, ...]:
    """Every `table.key` of the settings that has a value with no file, in their order."""
    tables = msgspec.structs.fields(Effective)
    shapes = (field for field in tables if isinstance(field.type, type))
    return tuple(
        f"{shape.name}.{key.name}"
        for shape in shapes
        if shape.name != "tracker"
        for key in msgspec.structs.fields(shape.type)
    )


def held(tables: Tables, name: str) -> dict[str, str]:
    """Each `table.key` one file holds, and the file's name."""
    found: dict[str, str] = {}
    for table, body in tables.items():
        keys_held = body if isinstance(body, dict) else {}
        dotted = (f"{table}.{key}" for key in keys_held)
        found.update(dict.fromkeys(dotted, name))
    return found


def sources(files: Sequence[Named]) -> dict[str, str]:
    """Each `table.key` in force and the name of the file it comes from, or Lem's default."""
    found = dict.fromkeys(keys(), places.DEFAULT)
    for tables, name in reversed(files):
        found.update(held(tables, name))
    return found
