"""Each criterion of the plan with the tests that hold it and what the last check of them gave
(`board_model.criterion_checks` on `main`): not held when a test does not hold it, held by its
tests when each does."""

from typing import TYPE_CHECKING

from lem.board.inputs.task.criteria import Case, Criterion
from lem.board.inputs.text import Look
from lem.board.views.artifacts.documents import chart
from lem.board.views.criteria.tested import ENDED, said_of
from lem.records.base import Frozen

if TYPE_CHECKING:
    from lem.board.inputs.parts import Document
    from lem.records.criterion import Criterion as Stated
    from lem.records.record import Record


class State(Frozen, frozen=True, kw_only=True):
    """A criterion's state: its look, its icon and its word."""

    look: Look
    icon: str
    label: str | None = None


def criterion_of(record: Record, stated: Stated) -> Criterion:
    """A criterion of the plan, with each test and what its last check gave."""
    checks = [said_of(record, stated.number, test) for test in stated.tests]
    state = state_of(stated, [held for _, held in checks])
    return Criterion(
        id=f"criterion-{stated.number}",
        number=stated.number,
        look=state.look,
        icon=state.icon,
        text=stated.text,
        cases=(Case(steps=stated.case),) if stated.case else (),
        chart=charted(record, stated.number, stated.chart),
        tests=tuple(
            zip(commands_of(stated), [said for said, _ in checks], strict=True)
        ),
        no_test=no_test_of(record, stated),
        label=state.label,
    )


def charted(record: Record, number: int, source: str | None) -> Document | None:
    """A criterion's chart, or None."""
    if not source:
        return None
    slug = record.task.slug
    return chart(f"crit-{slug}-{number}", source)


def commands_of(stated: Stated) -> list[str]:
    """The command of each test of the criterion."""
    return [test.command for test in stated.tests]


def state_of(stated: Stated, held: list[bool | None]) -> State:
    """Not held when a test does not hold it, held when every test does, else neither."""
    if False in held:
        return State(look="bad", icon="triangle-exclamation", label="not held")
    if stated.tests and all(held):
        return State(look="done", icon="check", label="held by its tests")
    return State(look="quiet", icon="file-lines")


def no_test_of(record: Record, stated: Stated) -> str | None:
    """Why the criterion has no test, or that it has none yet."""
    if stated.tests:
        return None
    if stated.no_test:
        return f"no test: {stated.no_test}"
    return "no test" if record.task.status in ENDED else "no test yet"
