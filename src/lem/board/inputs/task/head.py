"""The header of a task's panel: its status with its time, its title, its key line, the owner's
acts, what was asked, its facts, its chips; and the tabs under it."""

from lem.board.inputs.forms import ActForm
from lem.board.inputs.parts import Chip, Input, Link, When
from lem.board.inputs.text import Href, Icon, Inline, Look, Plain


class Pill(Input, frozen=True, kw_only=True):
    """The task's status (`Waits for the merge`), its look, whether it moves, and how long it
    is in it (or how long ago it ended)."""

    look: Look
    label: Plain
    live: bool = False
    since: When


class KeyLine(Input, frozen=True, kw_only=True):
    """The one line the header keeps when it folds: the pull request with green or not green,
    else what the task waits for (the owner's thing, in his look), else its state's words."""

    link: Link | None = None
    word: Plain | None = None
    look: Look | None = None
    icon: Icon | None = None
    text: Inline | None = None


class Fact(Input, frozen=True, kw_only=True):
    """A fact of the header (Type, Careful, Waits for, Parked, Branch, Pull request, Session, In
    this state) or of the merge step: its key and term, its word in bold, its text, whether the
    text is a name in monospace, whether it is the owner's (his look), its hover, its link, its
    time, the line under it, the words a button copies, and the agterm session a button jumps
    to (on this Mac only)."""

    key: Plain
    term: Plain
    bold: Plain | None = None
    text: Inline | None = None
    mono: bool = False
    yours: bool = False
    title: Plain | None = None
    link: Link | None = None
    when: When | None = None
    sub: Inline | None = None
    copy: Plain | None = None
    jump: Plain | None = None


class HeadActs(Input, frozen=True, kw_only=True):
    """The owner's acts in the header, where the page may act: open a session, the link to the
    merge's confirm step (`Merge #44…`), or the merge that runs now."""

    session: ActForm | None = None
    merge: Link | None = None
    merging: bool = False


class Tab(Input, frozen=True, kw_only=True):
    """A tab of the panel: its key, its name, its address, its key on the keyboard, whether it
    is the one shown, and its count (the documents of Artifacts)."""

    key: Plain
    name: Plain
    href: Href
    kbd: Plain
    current: bool = False
    count: int | None = None


class TaskHead(Input, frozen=True, kw_only=True):
    """The header: the task's slug, the view it goes back to, its pill, its title, its key
    line, the owner's acts, what was asked (none when it says what the title says), its facts
    and its chips."""

    slug: Plain
    back: Href
    pill: Pill
    title: Plain
    key_line: KeyLine | None = None
    acts: HeadActs | None = None
    ask: Inline | None = None
    facts: tuple[Fact, ...] = ()
    chips: tuple[Chip, ...] = ()
