"""The sidebar of every page of a workspace: the repository and the beacon, the notices, what
waits for the owner (one row for each task, its most pressing thing first), the views, and the
rail it folds into."""

from typing import Literal

from lem.board.inputs.parts import Input, When
from lem.board.inputs.switcher import Switcher
from lem.board.inputs.text import Href, Icon, Inline, Look, Plain


class Notice(Input, frozen=True, kw_only=True):
    """A notice at the top of the sidebar: its id and kind (demo data, the owner away, a
    blocked task, a status no stage writes), its look and icon, its first words in bold, what
    it says, and the task it names."""

    id: Plain
    kind: Literal["demo", "away", "blocked", "unknown"]
    look: Look | None = None
    icon: Icon | None = None
    head: Plain | None = None
    said: Inline
    task: Href | None = None
    task_title: Plain | None = None


class Waiting(Input, frozen=True, kw_only=True):
    """A task that waits for the owner, as one row: its id, the task, the look and icon of its
    first thing, its verb (`Read the breaker of gift-note-in-export`), since when and what that
    time is, the task's title, how many things of it wait when two or more, where the row goes,
    its hover (the verb, the task and where he answers), and whether its task is the one
    open."""

    id: Plain
    slug: Plain
    look: Look
    icon: Icon
    verb: Inline
    since: When
    task: Plain
    things: int = 1
    href: Href
    title: Plain
    selected: bool = False


class ViewButton(Input, frozen=True, kw_only=True):
    """A view of the workspace (Tasks, Waits for you, Backlog, Activity): its key, its words
    and icon, its address, its key on the keyboard, its hover on the folded rail (`5 tasks wait
    for you`, `Tasks · key T`), its count and that count's hover (none where the view counts
    nothing or did not read), whether it is the view shown, and its look."""

    key: Plain
    label: Plain
    icon: Icon
    href: Href
    kbd: Plain
    rail_title: Plain
    count: int | None = None
    count_title: Plain | None = None
    current: bool = False
    look: Look | None = None


class Flag(Input, frozen=True, kw_only=True):
    """A mark on the folded rail (demo data, the owner away, tasks stopped, another workspace
    where something waits): its look, its hover, its count, and where it goes when it is a
    link."""

    kind: Plain
    look: Look | None = None
    title: Plain
    count: int | None = None
    href: Href | None = None


class Sidebar(Input, frozen=True, kw_only=True):
    """The sidebar: the repository and its hover (`shop · tasks land on main`), the beacon's
    hover and whether it is bad, the notices, the head of what waits (its count and hover), one
    row for each task that waits, the views, the flags of the folded rail, and the switcher of
    the workspaces."""

    repo: Plain
    repo_title: Plain
    beacon: Plain
    beacon_bad: bool = False
    notices: tuple[Notice, ...] = ()
    waits_count: int
    waits_title: Plain
    waits: tuple[Waiting, ...] = ()
    views: tuple[ViewButton, ...]
    flags: tuple[Flag, ...] = ()
    switcher: Switcher
