"""A page of a workspace whole: its frame (the head, the bars, the sidebar, the search, the
keys) and the one view and panel the address shows."""

from lem.board.inputs.activity import Activity, NewTask
from lem.board.inputs.backlog import Backlog
from lem.board.inputs.layout import Head, Keys, Phonebar, Statusbar, Topbar, Viewer
from lem.board.inputs.parts import Input, Note
from lem.board.inputs.search import Search
from lem.board.inputs.sidebar import Sidebar
from lem.board.inputs.task.panel import Panel
from lem.board.inputs.tasks import Older, Tasks
from lem.board.inputs.waits import Waits


class Frame(Input, frozen=True, kw_only=True):
    """What every page of a workspace has around its view: who asks, the head, the phone's
    bar, the sidebar, the bar above the view, the status bar, the search, the view's keys, and
    whether its tasks are examples (`lem board --demo`)."""

    viewer: Viewer
    head: Head
    phonebar: Phonebar
    sidebar: Sidebar
    topbar: Topbar
    statusbar: Statusbar
    search: Search
    keys: Keys | None = None
    demo: bool = False


class Page(Input, frozen=True, kw_only=True):
    """A page of a workspace: its frame, the result of an act above the view, the one view of
    its address, and the panel of the task it opens."""

    frame: Frame
    note: Note | None = None
    tasks: Tasks | None = None
    older: Older | None = None
    waits: Waits | None = None
    backlog: Backlog | None = None
    activity: Activity | None = None
    new: NewTask | None = None
    panel: Panel | None = None
