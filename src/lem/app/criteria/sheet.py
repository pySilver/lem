"""The fast track's `criteria.md` in the task's folder, read (`criteria.parse` on `main`, its
plain form).

The file holds `## Acceptance criteria`, then `Size: small, because ...`, then the numbered
criteria, each with `- test: `COMMAND` in `FILE`` or `- no test: REASON` lines under it; any other
line under a criterion is more of its text. A plan's section, the steps of a case, a chart and a
code fence are the step `criteria`'s, with this reader's place in `model/criteria`.
"""

import re
from types import MappingProxyType
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.records.approvals import Size
from lem.records.base import Frozen
from lem.records.criterion import Criterion, CriterionTest

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path


NAME = "criteria.md"
HEADING = "## Acceptance criteria"
SIZE = re.compile(r"^Size:\s*(small|full)\s*(?:,\s*because|:)\s*(.+)$", re.IGNORECASE)
NUMBERED = re.compile(r"^(\d+)\.\s+(.+)$")
TEST = re.compile(r"^\s+-\s+test:\s+`([^`]+)`\s+in\s+(.+)$")
NO_TEST = re.compile(r"^\s+-\s+no test:\s+(.+)$")
QUOTED = re.compile(r"`([^`]+)`")
SIZES: Mapping[str, Size] = MappingProxyType({"small": "small", "full": "full"})


class Sheet(Frozen, frozen=True, kw_only=True):
    """What `criteria.md` says: the size and why, and the criteria."""

    size: Size
    why: str
    criteria: tuple[Criterion, ...]


def wrong(path: Path, line: str) -> Refusal:
    """The refusal of a line of `criteria.md` that is not of its form."""
    said = line.strip()
    return Refusal(
        "criteria-form",
        f"{path}: {said!r} is not a line of the criteria's form",
        f"{HEADING}, then Size: small, because WHY, then 1. THE CRITERION, with "
        "- test: `COMMAND` in `FILE` or - no test: REASON under it",
    )


def under(criterion: Criterion, line: str) -> Criterion:
    """The criterion with one more line under it: a test, why it has none, or more text."""
    test, none = TEST.match(line), NO_TEST.match(line)
    if test:
        files = tuple(QUOTED.findall(test[2]))
        tests = (*criterion.tests, CriterionTest(command=test[1], files=files))
        return replace(criterion, tests=tests)
    if none:
        return replace(criterion, no_test=none[1].strip())
    return replace(criterion, text=f"{criterion.text} {line.strip()}")


def added(found: list[Criterion], line: str, path: Path) -> list[Criterion]:
    """The criteria with one more line: a numbered criterion, or a line under the last."""
    numbered = NUMBERED.match(line)
    number = len(found) + 1
    if numbered and int(numbered[1]) == number:
        return [*found, Criterion(number=number, text=numbered[2].strip())]
    if numbered or not found:
        raise wrong(path, line)
    last = under(found[-1], line)
    return [*found[:-1], last]


def lines_of(path: Path) -> list[str]:
    """The lines of the section after its heading that are not blank."""
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    section = text.partition(HEADING)[2]
    return [line for line in section.splitlines() if line.strip()]


def heading_of(path: Path) -> tuple[Size, str, list[str]]:
    """The size and why of the section's first line, and the lines after it."""
    lines = lines_of(path) or [f"no {HEADING} with a Size line"]
    matched = SIZE.match(lines[0].strip())
    if matched is None:
        raise wrong(path, lines[0])
    named, why = matched.groups()
    kind = SIZES[named.lower()]
    return kind, why.strip(), lines[1:]


def sheet_of(path: Path) -> Sheet:
    """Read `criteria.md` at `path`."""
    size, why, rest = heading_of(path)
    found: list[Criterion] = []
    for line in rest:
        found = added(found, line, path)
    return Sheet(size=size, why=why, criteria=tuple(found))
