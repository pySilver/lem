"""The large card of a task's Overview, what it does now and who acts; and its progress: the
phases, the ring of its plan, and its numbers."""

from lem.board.inputs.forms import AnswerForm, Way
from lem.board.inputs.parts import Input, When
from lem.board.inputs.text import Icon, Inline, Look, Plain


class Foot(Input, frozen=True, kw_only=True):
    """The card's foot: when the task last moved, how long it is in its state (or when it
    ended), what that time is, and the agterm session a button jumps to (on this Mac only)."""

    updated: When
    timer: When
    note: Plain
    jump: Plain | None = None


class Now(Input, frozen=True, kw_only=True):
    """What the task does now: its look and icon, whether it moves, its hover, Lem's first line
    of it, who acts (`You act`), its head, its state's words and the lines beside them, what its
    investigation found and where the report is, where the owner answers, the words of a breaker
    that waits, the ways to its session and to the Inbox, the answer the board takes here, and
    the foot."""

    look: Look
    icon: Icon
    live: bool = False
    title: Plain | None = None
    opening: Inline | None = None
    who: Plain
    head: Inline
    shown: Inline | None = None
    more: Inline | None = None
    found: Inline | None = None
    report: Plain | None = None
    where: Inline | None = None
    breaker: Plain | None = None
    ways: tuple[Way, ...] = ()
    answer: AnswerForm | None = None
    foot: Foot


class Phase(Input, frozen=True, kw_only=True):
    """A phase of the task (Criteria, Plan, Build, Checks, Review, Proposed, Landed; Change on
    the fast track; Investigation first when it was investigated): its name, its line
    (`task 2 of 2`, `2 green`), and whether it is past or the one now."""

    name: Plain
    sub: Plain | None = None
    past: bool = False
    current: bool = False


class Ring(Input, frozen=True, kw_only=True):
    """The ring of the plan's tasks: the finished, the current, the whole, and its words
    (`2/2`, `plan tasks`)."""

    done: int
    current: int
    total: int
    big: Plain
    small: Plain


class Stat(Input, frozen=True, kw_only=True):
    """A number of the task (Who works on it, Last commit, Open for, Checks, Review,
    Decisions): its label, its value, what it says under it, and its look."""

    label: Plain
    shown: Plain
    when: When | None = None
    said: Plain
    look: Look | None = None


class Phases(Input, frozen=True, kw_only=True):
    """The progress card: the look of its phases, the phases, the ring, and the numbers."""

    look: Look
    phases: tuple[Phase, ...]
    ring: Ring
    stats: tuple[Stat, ...]
