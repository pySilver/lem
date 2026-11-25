"""A criteria section read up to one line: its first line is its Size line, then the numbered
criteria, each with what is under it (`criteria.parse` on `main`)."""

import re

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.criteria import lines
from lem.records.approvals import Size
from lem.records.base import Frozen
from lem.records.criterion import Criterion

SIZE = re.compile(
    r"^Size:\s*(full|small)\s*(?:,\s*because|:|—|-)\s*(\S.*)$", re.IGNORECASE
)
NUMBERED = re.compile(r"^(\d+)\.\s+(.+)$")


class Draft(Frozen, frozen=True, kw_only=True):
    """The size and why once the first line is read, and the criteria so far."""

    size: Size | None = None
    why: str = ""
    criteria: tuple[Criterion, ...] = ()


def sized(line: str, where: str) -> Draft:
    """The draft the section's first line gives: its size and why."""
    said = line.strip()
    found = SIZE.match(said)
    if found is None:
        raise Refusal(
            lines.CODE,
            f"{where}: the section starts with its Size line, and this line is {said!r}",
            "write Size: full, because WHY, or Size: small, because WHY",
        )
    size: Size = "small" if found[1].lower() == "small" else "full"
    return Draft(size=size, why=found[2].strip())


def numbered(draft: Draft, line: str, where: str) -> Draft:
    """The draft with one more criterion, which `line` opens with its number."""
    known = draft.criteria
    number = len(known) + 1
    found = NUMBERED.match(line)
    if found is None or int(found[1]) != number:
        raise Refusal(
            lines.CODE,
            f"{where}: {line.strip()!r} is not criterion {number}",
            "number the criteria 1, 2, 3 in order, as in 1. A rule, with one example; "
            "the steps of a criterion's case go indented under its sentence",
        )
    criterion = Criterion(number=number, text=found[2].strip())
    return replace(draft, criteria=(*known, criterion))


def taken(draft: Draft, line: str, where: str) -> Draft:
    """The draft with one more line that is not blank and not code."""
    if draft.size is None:
        return sized(line, where)
    known = draft.criteria
    if NUMBERED.match(line) or not known:
        return numbered(draft, line, where)
    last = lines.under(known[-1], line, where)
    return replace(draft, criteria=(*known[:-1], last))


def charted(draft: Draft, chart: str | None, where: str) -> Draft:
    """The draft whose last criterion has its chart; a second chart is refused."""
    if not draft.criteria:
        return draft
    *before, last = draft.criteria
    if last.chart is not None:
        raise Refusal(
            lines.CODE,
            f"{where}: criterion {last.number} has a chart already",
            "one chart for one criterion; a chart of several goes under ## How it works, "
            "after the section",
        )
    return replace(draft, criteria=(*before, replace(last, chart=chart)))
