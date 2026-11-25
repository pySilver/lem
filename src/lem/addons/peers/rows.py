"""Workspace rows from a peer, with addresses made at the entry board."""

import json
from urllib.parse import quote

import msgspec

from lem.records.base import Frozen

SPACES = "Lem-Spaces"
# The old board leaves room within its header line limit (main, 2026-11-25).
SPACES_CAP = 32_000


class Row(Frozen, frozen=True, kw_only=True):
    """A workspace's displayed facts, apart from any actions."""

    name: str
    path: str = ""
    host: str = ""
    url: str = ""
    waits: int | None = None
    building: int | None = None
    checks: int | None = None
    running: int | None = None
    problem: str | None = None
    reachable: bool | None = None
    answered: int | None = None
    said: str = ""

    def on_entry(self) -> Row:
        """Quote the machine's name before making a local link from it."""
        host = quote(self.host, safe="")
        return located(self, host)


def located(row: Row, host: str) -> Row:
    """Make an entry-board link without taking an address from a peer."""
    named = quote(row.name, safe="")
    return msgspec.structs.replace(
        row, host=host, url=f"/{host}/{named}/" if named else ""
    )


def gray(row: Row, answered: int | None, said: str) -> Row:
    """Retain the workspace and answer time and remove the old counts."""
    return msgspec.structs.replace(
        row,
        reachable=False,
        answered=answered,
        said=said,
        waits=None,
        building=None,
        checks=None,
        running=None,
    )


def ordered(row: Row) -> tuple[bool, int, str, str]:
    """Put the reachable machines and the rows that wait first."""
    priority = -(row.waits or 0)
    return row.reachable is False, priority, row.host, row.name


def header(rows: tuple[Row, ...]) -> str | None:
    """Encode a bounded list of switcher rows for the peer."""
    packed = msgspec.to_builtins(rows)
    encoded = json.dumps(packed, ensure_ascii=True, separators=(",", ":"))
    return encoded if len(encoded) <= SPACES_CAP else None


def from_header(given: str) -> tuple[Row, ...]:
    """Ignore a malformed or oversized switcher header."""
    if len(given) > SPACES_CAP:
        return ()
    try:
        rows = msgspec.json.decode(given, type=tuple[Row, ...])
    except msgspec.DecodeError, RecursionError:
        return ()
    present = (row for row in rows if row.host)
    return tuple(row.on_entry() for row in present)


def with_own(
    given: tuple[Row, ...], own: tuple[Row, ...], host: str
) -> tuple[Row, ...]:
    """Keep the entry's other machines, and replace its copy of this one."""
    others = tuple(row for row in given if row.host != host)
    return tuple(sorted((*others, *own), key=ordered))
