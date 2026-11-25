"""The criteria on the tab Criteria and decisions: each criterion with its case, its chart and
its tests; a change of them with its before and after; and the owner's yes."""

from typing import Literal

from lem.board.inputs.forms import ActForm, AnswerForm
from lem.board.inputs.parts import Document, Input, Link, Note
from lem.board.inputs.text import Icon, Inline, Look, Plain


class Case(Input, frozen=True, kw_only=True):
    """One run of a case: its label, when it has one (`Today`, `After`), and its steps."""

    label: Plain | None = None
    steps: tuple[Inline, ...]


class Criterion(Input, frozen=True, kw_only=True):
    """A criterion: its id and number, its look and icon (held by its tests, not held, not
    checked), its sentence, its case, its chart, each test with what it showed (`passes on the
    branch, fails on the base commit`), why it has no test, its state's word (`held by its
    tests`), and the note over every criterion when they stand apart from the plan."""

    id: Plain
    number: int
    look: Look
    icon: Icon
    text: Inline
    cases: tuple[Case, ...] = ()
    chart: Document | None = None
    tests: tuple[tuple[Plain, Plain], ...] = ()
    no_test: Plain | None = None
    label: Plain | None = None
    note: Plain | None = None


class Side(Input, frozen=True, kw_only=True):
    """One side of a criterion's change (`Before · criterion 1`): its label, its sentence and
    its steps."""

    label: Plain
    text: Inline
    steps: tuple[Inline, ...] = ()


class Pair(Input, frozen=True, kw_only=True):
    """A criterion changed, removed or added, with its sides."""

    change: Literal["changed", "removed", "added"]
    sides: tuple[Side, ...]


class Change(Input, frozen=True, kw_only=True):
    """The change of the criteria from the owner's note: what it says (`Lem changed them from
    your note “…”.`), why the text before does not read, when it does not, and the pairs."""

    said: Inline
    error: Plain | None = None
    pairs: tuple[Pair, ...] = ()


class Approve(Input, frozen=True, kw_only=True):
    """The owner's yes to the criteria: its label (`Approve the criteria`), its head, the line
    of the personas' read, the act's result when this card holds it, the change from his note,
    the criteria as written, their plain text (for a page with no script), his answer here
    (Yes, or No with his note) or the form of the yes alone, its words, the way back, the answer
    already on record, the words where the page may not act, and whether it is a sheet that a
    phone reads to its end first."""

    label: Plain
    head: Plain
    read: Plain | None = None
    note: Note | None = None
    change: Change | None = None
    criteria: Document | None = None
    plain: Plain | None = None
    answer: AnswerForm | None = None
    form: ActForm | None = None
    say: Plain | None = None
    back: Link | None = None
    took: Plain | None = None
    words: Plain | None = None
    sheet: bool = False
