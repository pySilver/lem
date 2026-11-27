"""One row of `lem doctor`, and the report of all of them.

A row says what the check looked for, whether it found it, what it found, what Lem uses it for,
what happens without it, and the way to it: a guide to install it by, or the line that sets it.
A program that Homebrew ships names its formula or its cask, and a skill or a hook that a recipe
installs names the recipe, which `/lem init` follows on the owner's `install`.
Its need says what a row that is not found costs: a `required` row fails the check, a
`recommended` or `optional` row only says so, and a `project` row is about the repository the
check runs in, never about the machine, and never fails it.
"""

from typing import TYPE_CHECKING, Literal

import msgspec

from lem.cli.doctor import brew

if TYPE_CHECKING:
    from collections.abc import Callable

    from lem.cli.doctor.look import Look

type Need = Literal["required", "recommended", "optional", "project"]

REQUIRED: Need = "required"
RECOMMENDED: Need = "recommended"
OPTIONAL: Need = "optional"
PROJECT: Need = "project"


class Row(msgspec.Struct, frozen=True, kw_only=True, omit_defaults=True):
    """One thing the check looked for, and what it found."""

    name: str
    need: Need
    found: bool
    detail: str | None
    used_for: str
    without_it: str | None
    guide: str | None = None
    line: str | None = None
    lines: tuple[str, ...] = ()
    signed_in: bool | None = None
    in_session: bool | None = None
    running: bool | None = None
    formula: str | None = None
    cask: str | None = None
    recipe: str | None = None


type Found = Row | tuple[Row, ...]
# One part of the check: the name and need of its row when it is refused, and what it looks at.
type Part = tuple[str, Need, Callable[[Look], Found]]


class Report(msgspec.Struct, frozen=True, kw_only=True):
    """Every row, whether each required one was found, and the lines that install through
    Homebrew each required or recommended program that is absent."""

    ok: bool
    rows: tuple[Row, ...]
    brew: tuple[str, ...] = ()


def missing(row: Row) -> bool:
    """Whether `row` is required and not found."""
    return row.need == REQUIRED and not row.found


def failing(rows: tuple[Row, ...]) -> tuple[Row, ...]:
    """The required rows that were not found."""
    return tuple(filter(missing, rows))


def wanted(row: Row) -> bool:
    """Whether `row` is a required or recommended row that was not found."""
    return row.need in {REQUIRED, RECOMMENDED} and not row.found


def brewed(rows: tuple[Row, ...]) -> tuple[str, ...]:
    """The Homebrew lines of the required and recommended rows not found. An optional program
    keeps its own line in its row."""
    absent = tuple(filter(wanted, rows))
    formulas = [row.formula for row in absent if row.formula]
    return brew.lines(formulas, [row.cask for row in absent if row.cask])


def reported(rows: tuple[Row, ...]) -> Report:
    """The report of `rows`."""
    return Report(ok=not failing(rows), rows=rows, brew=brewed(rows))
