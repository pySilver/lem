"""One acceptance criterion, as the plan or `criteria.md` states it."""

from lem.records.base import Frozen


class CriterionTest(Frozen, frozen=True, kw_only=True):
    """A test that shows a criterion: the command, and the files it runs."""

    command: str
    files: tuple[str, ...] = ()


class Criterion(Frozen, frozen=True, kw_only=True):
    """A criterion: its number, its sentence, the steps of its case, its chart, and its tests,
    or why it has none (both together are refused); and in the criteria of a feature, the
    heading of the part it belongs to, None for the group of the whole feature. A task with no
    parts writes no `part`, so the marks of its criteria are what they were without the key."""

    number: int
    text: str
    case: tuple[str, ...] = ()
    chart: str | None = None
    tests: tuple[CriterionTest, ...] = ()
    no_test: str | None = None
    part: str | None = None
