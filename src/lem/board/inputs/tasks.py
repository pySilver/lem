"""The view Tasks, `/HOST/WORKSPACE/`: the tasks in four columns by who acts, each a card, and
Done's foot row to the older ended tasks."""

from lem.board.inputs.parts import Chip, Input, Link, When
from lem.board.inputs.text import Href, Inline, Look, Plain


class Progress(Input, frozen=True, kw_only=True):
    """The bar of a task that builds its plan: task `at` of `of`, its hover, and the bar's done
    part and current part, each a percent of its width."""

    at: int
    of: int
    title: Plain
    done: float
    width: float


class TaskCard(Input, frozen=True, kw_only=True):
    """A task on its column: its slug and title, where it opens, what was asked (none when it
    says what the title says), its status and look (`s-held`, `a-you`), its line and that line's
    hover, whether the line moves, since when it is in its state (or how long ago it ended), the
    bar of its plan, its chips, and whether it is the task open."""

    slug: Plain
    title: Plain
    href: Href
    ask: Plain | None = None
    status: Plain
    look: Look
    line: Inline
    line_title: Plain | None = None
    live: bool = False
    since: When
    progress: Progress | None = None
    chips: tuple[Chip, ...] = ()
    selected: bool = False


class Column(Input, frozen=True, kw_only=True):
    """A column: its key and look, its title, its total before any limit on its cards, its
    words when empty, whether the owner folded it, its cards, and Done's link to the tasks
    it has no card for."""

    key: Plain
    look: Look
    title: Plain
    total: int
    empty: Plain
    folded: bool = False
    cards: tuple[TaskCard, ...] = ()
    older: Link | None = None


class Tasks(Input, frozen=True, kw_only=True):
    """The four columns: Waits for you, Building, Checks and review, Done."""

    columns: tuple[Column, ...]


class Ended(Input, frozen=True, kw_only=True):
    """An ended task Done has no card for: its slug and title, where it opens, its look, icon
    and status's words (`Landed`), its pull request, and when it ended."""

    slug: Plain
    title: Plain
    href: Href
    look: Look
    icon: Plain
    label: Plain
    pull: Chip | None = None
    ended: When


class Older(Input, frozen=True, kw_only=True):
    """The page `/HOST/WORKSPACE/done`: the ended tasks Done has no card for, the newest
    first, the link back to the newer ones in Done, and the words when there is none."""

    rows: tuple[Ended, ...] = ()
    newer: Link
    empty: Plain | None = None
