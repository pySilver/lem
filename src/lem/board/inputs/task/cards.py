"""The cards of a task's Overview above its large card: the answer already on record, the
`lem-ask` cards of its session, the merge review, a park, a breaker, what we are building, and
green or not green."""

from lem.board.inputs.forms import AnswerForm, Way
from lem.board.inputs.parts import Document, Input, Link, When
from lem.board.inputs.text import Href, Icon, Inline, Look, Plain
from lem.board.inputs.waits import Reasons


class Asked(Input, frozen=True, kw_only=True):
    """A card the task's session put up and the owner has not answered: its page, its
    prompt, the link to it (where the page may act), and since when."""

    page: Plain
    prompt: Inline
    link: Link | None = None
    since: When


class Review(Input, frozen=True, kw_only=True):
    """The merge agent's review of an open pull request: whether it calls the owner, its head
    (`The merge review · it calls you`), its verdict's words as its hover, when it was written,
    its text, and its file on Artifacts."""

    calls: bool
    head: Plain
    why: Plain | None = None
    at: When | None = None
    text: Document
    artifact: Link


class Breaker(Input, frozen=True, kw_only=True):
    """The breaker that stopped the build: whether it waits for the owner, its head (`The
    build stopped · breaker 1`), its cause's words as its hover, when it stopped, its document,
    or why the board has none, the links to the document and the handoff, where the owner
    answers, his answer here, and the ways to the session, the Inbox and the lines he types."""

    waits: bool
    head: Plain
    why: Plain
    at: When
    document: Document | None = None
    missing: Plain | None = None
    artifact: Link
    handoff: Link | None = None
    where: Inline | None = None
    answer: AnswerForm | None = None
    ways: tuple[Way, ...] = ()


class Picture(Input, frozen=True, kw_only=True):
    """A picture of the task's media: its address, the address of its full size, and its
    words."""

    src: Href
    href: Href
    alt: Plain


class Shot(Input, frozen=True, kw_only=True):
    """A before and an after of one thing (`media/receipt-before.png`, `-after.png`): its id,
    its caption (`Receipt`), and the two pictures."""

    id: Plain
    caption: Plain
    before: Picture | None = None
    after: Picture


class Building(Input, frozen=True, kw_only=True):
    """What we are building: the goal, the outcome of `task.md`, the before and after
    pictures its text does not show, the link to the important decisions that wait for a look,
    the line of the backlog items filed on the task's branch (none when git cannot tell), and
    each item's title and path."""

    goal: Plain
    outcome: Document | None = None
    shots: tuple[Shot, ...] = ()
    important: Link | None = None
    filed: Plain | None = None
    on_branch: tuple[tuple[Plain, Plain], ...] = ()


class Verdict(Input, frozen=True, kw_only=True):
    """Green or not green: its look and icon, its word (`not green, for 4 reasons:`), its
    text, and the reasons."""

    look: Look
    icon: Icon
    word: Plain
    text: Inline | None = None
    reasons: Reasons | None = None
