"""The marks of a set of criteria (`criteria.text_digest`, `criteria.shown_digest` and
`state.whole` on `main`).

A criterion's whole text is its sentence and the steps of its case, one to a line: what an
approval keeps, what a recorded change names, and what the personas' read marks. Its chart is no
part of it, and each run of spaces counts as one, so how a criterion is broken into lines does not
count. The mark of the criteria with their tests says which set a check ran on; the mark of a
file's bytes says which text the owner's page showed him.
"""

import hashlib
from typing import TYPE_CHECKING

import msgspec
from msgspec.structs import replace

if TYPE_CHECKING:
    from lem.records.approvals import Size
    from lem.records.criterion import Criterion

# The hex digits of a mark of criteria, and of a file's bytes as a page showed them.
LENGTH = 12
SHOWN = 16


def whole(criterion: Criterion) -> str:
    """A criterion's sentence and the steps of its case, one to a line."""
    return "\n".join((criterion.text, *criterion.case))


def same(one: str, other: str) -> bool:
    """Whether two texts of a criterion differ in runs of spaces only."""
    return one.split() == other.split()


def flat(criteria: tuple[Criterion, ...]) -> list[str]:
    """Each criterion's whole text, each run of spaces as one."""
    return [" ".join(whole(criterion).split()) for criterion in criteria]


def of_texts(size: Size, criteria: tuple[Criterion, ...]) -> str:
    """The mark of the size and the criteria's whole texts, without their tests: what an
    approval keeps and a read names."""
    return marked(msgspec.json.encode([size, flat(criteria)]), LENGTH)


def of_tests(size: Size, criteria: tuple[Criterion, ...]) -> str:
    """The mark of the size and the criteria with their cases and tests, their charts not: a
    result of a check belongs to the set it ran on."""
    charted = [replace(criterion, chart=None) for criterion in criteria]
    return marked(msgspec.json.encode([size, charted]), LENGTH)


def shown(raw: bytes) -> str:
    """The mark of a criteria file's bytes as the owner's page showed them, which the board's
    form and `lem criteria approve --shown` carry back."""
    return marked(raw, SHOWN)


def marked(body: bytes, length: int) -> str:
    """The first `length` hex digits of the sha256 of `body`."""
    return hashlib.sha256(body).hexdigest()[:length]
