"""The tab Overview of a task, `/HOST/WORKSPACE/tasks/SLUG`: its cards in their order; and what
a task whose events became one summary (`lem prune`) says in their place."""

from lem.board.inputs.parts import Input, Link, Note
from lem.board.inputs.task.cards import Asked, Breaker, Building, Review, Verdict
from lem.board.inputs.task.now import Now, Phases
from lem.board.inputs.text import Inline, Plain


class Answered(Input, frozen=True, kw_only=True):
    """The owner's answer on record, which the task's session takes: what took effect (`You
    picked Drop for breaker 1 at 15:40, from the phone`), and his note."""

    took: Plain
    note: Inline | None = None


class Put(Input, frozen=True, kw_only=True):
    """A task the owner parked: since when, why, and the line that brings it back."""

    since: Plain
    why: Inline
    resume: Plain


class Pruned(Input, frozen=True, kw_only=True):
    """A task whose events became one summary: how many events, what it keeps, what went with
    them, what its folder holds now, and the link to its Artifacts."""

    events: Plain
    kept: Plain
    went: Plain
    files: Plain
    artifacts: Link


class Went(Input, frozen=True, kw_only=True):
    """A tab of a pruned task (Criteria and decisions, Checks and review, Timeline): what went
    with its events, and the link to its Artifacts."""

    id: Plain
    said: Plain
    artifacts: Link


class Overview(Input, frozen=True, kw_only=True):
    """The tab: the result of an act, the summary of a pruned task, the answer on record, the
    session's cards and their line, the merge review, the park, the breaker, what we are
    building, green or not green, the large card, and the progress (none for a pruned task)."""

    note: Note | None = None
    pruned: Pruned | None = None
    answered: Answered | None = None
    cards: tuple[Asked, ...] = ()
    cards_said: Plain | None = None
    review: Review | None = None
    parked: Put | None = None
    breaker: Breaker | None = None
    building: Building | None = None
    verdict: Verdict | None = None
    now: Now
    phases: Phases | None = None
