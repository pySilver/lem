"""The view Waits for you, `/HOST/WORKSPACE/waits`: one row for each thing the owner does, a
task's two things or more in one stack, the most pressing first; then the tasks he parked.

The reasons a pull request is not green, which the merge row, the Overview, Checks and review
and the merge step each list, are `Reasons`.
"""

from lem.board.inputs.forms import ActForm, AnswerForm
from lem.board.inputs.parts import Chip, Input, Link, When
from lem.board.inputs.text import Href, Icon, Inline, Look, Markdown, Plain


class Reason(Input, frozen=True, kw_only=True):
    """A reason a pull request is not green: its head (`Decision 1 was taken without the
    owner`), what it is about, its lines under it, and the decision or breaker it names."""

    head: Inline
    about: Inline | None = None
    detail: tuple[Inline, ...] = ()
    ref: Link | None = None


class Reasons(Input, frozen=True, kw_only=True):
    """The list of the reasons, under its id (`wr-refund-line-on-receipt`), each folded open
    by its own id `{id}-r{n}`."""

    id: Plain
    rows: tuple[Reason, ...] = ()


class Acts(Input, frozen=True, kw_only=True):
    """What the owner does on a row, where the page may act: the answer to its question (a
    breaker, a plan, a skip, a criterion of the fast track, whose text comes first), the links
    to a confirm step or a card (`Merge…`, `Park it…`, `Answer the card…`, `Read and
    approve…`), a merge that runs (`Merging…`), and a form (`Open a session`)."""

    criterion: Markdown | None = None
    answer: AnswerForm | None = None
    links: tuple[Link, ...] = ()
    busy: Plain | None = None
    forms: tuple[ActForm, ...] = ()


class Wait(Input, frozen=True, kw_only=True):
    """One thing the owner does: its id and kind, its look and icon, its verb and where it
    goes, the agterm session its verb jumps to (on this Mac only), since when and what that
    time is, the task's title and status's words, what it is about and its line, its marks
    (green, the pull request), the reasons it is not green, his acts, and where he answers."""

    id: Plain
    kind: Plain
    look: Look
    icon: Icon
    verb: Inline
    href: Href
    jump: Plain | None = None
    since: When
    task: Plain
    state: Plain
    what: Inline | None = None
    sub: Inline | None = None
    marks: tuple[Chip, ...] = ()
    reasons: Reasons | None = None
    acts: Acts | None = None
    where: Inline


class Stack(Input, frozen=True, kw_only=True):
    """The things of one task, in the place of its first: its slug and id, the look and icon
    of the first, its title, how many (`2 things`), the first's verb and the task's status's
    words, and each thing. A stack of one thing is that thing's row alone."""

    slug: Plain
    id: Plain
    look: Look
    icon: Icon
    title: Plain
    count: Plain
    first: Inline
    state: Plain
    waits: tuple[Wait, ...]


class Parked(Input, frozen=True, kw_only=True):
    """A task the owner put aside: its slug and title, where it opens, since when, why, the
    breaker that stopped its build, and the line that brings it back."""

    slug: Plain
    title: Plain
    href: Href
    since: When
    parked_at: Plain
    why: Inline
    breaker: Inline | None = None
    resume: Plain


class Waits(Input, frozen=True, kw_only=True):
    """The view: the stacks, the most pressing first, and the parked tasks."""

    stacks: tuple[Stack, ...] = ()
    parked: tuple[Parked, ...] = ()
