"""The workspaces of the machines, as the switcher at the foot of the sidebar and the page at
`/` show them: each with what waits and what runs there, or why it does not answer."""

from lem.board.inputs.parts import Chip, Input
from lem.board.inputs.text import Href, Plain


class Space(Input, frozen=True, kw_only=True):
    """A workspace of a machine: its id, its name (`studio/shop` with two machines), its path,
    what it says (`2 wait for you · 3 build`, `not reachable · last answer 5m ago`), the
    address of its board, whether it is this board, whether something waits there, and whether
    its machine answers."""

    id: Plain
    name: Plain
    host: Plain | None = None
    path: Plain | None = None
    says: Plain
    href: Href | None = None
    here: bool = False
    waits: bool = False
    reachable: bool = True


class Group(Input, frozen=True, kw_only=True):
    """The workspaces of one machine, under its name (`Workspaces` with one machine)."""

    id: Plain | None = None
    head: Plain
    spaces: tuple[Space, ...]


class Switcher(Input, frozen=True, kw_only=True):
    """The switcher: this workspace's name and machine, its hover, how many other workspaces
    have something that waits and that count's hover, the groups of its menu (none with one
    workspace), the menu's words, and the words of the link to every workspace."""

    name: Plain
    host: Plain | None = None
    title: Plain
    waiting: int = 0
    waiting_title: Plain | None = None
    groups: tuple[Group, ...] = ()
    menu: Plain | None = None
    every: Plain | None = None


class Box(Input, frozen=True, kw_only=True):
    """A workspace on the page of every workspace: its id, its name, its path, its board's
    address (none when its machine does not answer), whether something waits there, and its
    chips (`2 wait for you`, `3 build · 1 in checks and review`, `not reachable`)."""

    id: Plain
    name: Plain
    path: Plain
    href: Href | None = None
    waits: bool = False
    title: Plain | None = None
    chips: tuple[Chip, ...] = ()


class Workspaces(Input, frozen=True, kw_only=True):
    """The page at `/`: the machine, the line of how many repositories use Lem and where, the
    workspaces, the waiting first and the unreachable last, or none yet."""

    host: Plain
    ask: Plain
    boxes: tuple[Box, ...] = ()


class Failure(Input, frozen=True, kw_only=True):
    """A page that failed or a machine that does not answer: its title, what happened, and
    the fix, when there is one."""

    title: Plain
    said: Plain
    fix: Plain | None = None
