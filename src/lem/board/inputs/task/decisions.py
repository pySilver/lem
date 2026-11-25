"""The decisions on the tab Criteria and decisions: each with its story (the case, why it could
happen, this or that, who took it, its chart), a breaker with what it waits for; and the tab
whole."""

from typing import Literal

from lem.board.inputs.parts import Document, Input, Link, Note, Row
from lem.board.inputs.task.criteria import Approve, Case, Criterion
from lem.board.inputs.task.overview import Went
from lem.board.inputs.text import Inline, Look, Plain


class Option(Input, frozen=True, kw_only=True):
    """An option of a decision: its label (`B`) and what it leads to, whether it was taken, and
    the experts that picked it."""

    label: Plain
    leads: Inline | None = None
    taken: bool = False
    picked: tuple[Plain, ...] = ()


class Story(Input, frozen=True, kw_only=True):
    """A decision's story: its case and how it was had (`derived from the code, not run`), why
    it could happen, this or that, what was taken when none of these was, and who took it."""

    case_was: Plain | None = None
    cases: tuple[Case, ...] = ()
    cause: Inline | None = None
    options: tuple[Option, ...] = ()
    none_taken: Inline | None = None
    who: Inline | None = None


class Part(Input, frozen=True, kw_only=True):
    """A part of a decision's body (The decision, Important, The ladder, The personas, To undo;
    a breaker's Now, Its files, Where you answer): its label, its text, its lines, and its
    links."""

    label: Plain
    text: Inline | None = None
    lines: tuple[Inline, ...] = ()
    links: tuple[Link, ...] = ()


class Decision(Input, frozen=True, kw_only=True):
    """A decision or a breaker: its kind and id, its look, why it is important (open at first
    when it is), its mark (`important`, `breaker`), what was asked and what was chosen (a
    breaker's cause), who and when, its story, its chart, and its body's parts."""

    kind: Literal["decision", "breaker"] = "decision"
    id: int
    look: Look
    important: Plain | None = None
    mark: Plain | None = None
    what: Plain
    chose: Inline
    who: Plain
    story: Story | None = None
    chart: Document | None = None
    parts: tuple[Part, ...] = ()


class Criteria(Input, frozen=True, kw_only=True):
    """The tab Criteria and decisions: the result of an act when the approval card has no
    form, the owner's yes, the plan's `How it works`, the card of the criteria (its line, the
    rows of their read and approval, the criteria, or why there are none), the card of the
    decisions (its line, the decisions, a help that names no breaker, or why there is none),
    the words of a task that ended with neither, and what went with a pruned task's events."""

    note: Note | None = None
    approve: Approve | None = None
    how: Document | None = None
    criteria_said: Plain | None = None
    reads: tuple[Row, ...] = ()
    criteria: tuple[Criterion, ...] = ()
    criteria_empty: Plain | None = None
    decisions_said: Plain | None = None
    decisions: tuple[Decision, ...] = ()
    orphans: tuple[Row, ...] = ()
    decisions_empty: Plain | None = None
    ended: Plain | None = None
    went: Went | None = None
