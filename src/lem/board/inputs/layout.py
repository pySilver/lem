"""The frame of every page of a workspace: who asks for it, its head, the phone's bar, the bar
above the view, the status bar under it, and the keys of the view.

`Viewer` is what the request says (`main`'s `board_pages.Ctx`: the address, the cookie, the
listener and the client): a view takes it to make every address and to leave out what the page
may not do, and the template takes it for the classes of the frame.
"""

from lem.board.inputs.parts import Chip, Input, When
from lem.board.inputs.text import Href, Inline, Plain, View


class Viewer(Input, frozen=True, kw_only=True):
    """Who asks for the page: the machine and the workspace of its address and their base
    (`/studio/shop`), the view under the panel, the task, tab and file the address opens, and
    the question key and the owner's words sent to a confirm step. Whether the page is for
    this Mac (the agterm jump), whether it may act (on this Mac or through the
    tailnet door), whether it is the Hotwire Native app (every link a whole visit); and the
    cookie: the folded columns, the folded sidebar, the panel across the whole width, its width
    in pixels, and the task's header open."""

    host: Plain
    workspace: Plain
    base: Href
    view: View = "tasks"
    task: Plain | None = None
    tab: Plain = "overview"
    path: Plain | None = None
    key: Plain | None = None
    words: Plain | None = None
    local: bool = False
    may_act: bool = False
    native: bool = False
    folded: tuple[Plain, ...] = ()
    rail: bool = False
    full: bool = False
    width: int | None = None
    head_open: bool = False


class Head(Input, frozen=True, kw_only=True):
    """The page's head: its title (`Tasks · Lem · shop · 2 build · 5 for you`), the address of
    the workspace's stream and the version the page was drawn at, which the stream answers with
    a refresh when it moved, and the address of the agterm jump on a page for this Mac."""

    title: Plain
    stream: Href
    version: Plain
    jump: Href | None = None


class Phonebar(Input, frozen=True, kw_only=True):
    """The bar at the top of a phone: the workspace (`shop · demo data`), how many tasks wait
    for the owner and the words of its link, and the way to a new task where the page may
    act."""

    title: Plain
    waits: int
    waits_label: Plain
    new_task: Href | None = None


class Topbar(Input, frozen=True, kw_only=True):
    """The bar above the view: its name, what it holds in one line, the chips (the base
    branch, the pull requests proposed, the look at GitHub with its age, the tasks landed
    today), and the way to a new task where the page may act."""

    title: Plain
    summary: Plain
    chips: tuple[Chip, ...] = ()
    new_task: Href | None = None


class Statusbar(Input, frozen=True, kw_only=True):
    """The status bar: what did not read (each a problem, the page's look bad), when the
    workspace's files were read and how many events (`147 events`), the look at the forge with
    its age, hover and whether it failed, and the id of the line the stream writes `live` into."""

    problems: tuple[Plain, ...] = ()
    read: When
    events: Plain
    forge: Inline
    forge_title: Plain
    forge_bad: bool = False
    forge_when: When | None = None
    live: Plain


class KeyGroup(Input, frozen=True, kw_only=True):
    """Keys that do one thing (`J K ↑ ↓`), and the word of what they do (`move`)."""

    keys: tuple[Plain, ...]
    word: Plain


class Keys(Input, frozen=True, kw_only=True):
    """A line of a view's keys under the stage (`J K ↑ ↓ move · Enter open`): its id, and its
    groups."""

    id: Plain
    groups: tuple[KeyGroup, ...]
