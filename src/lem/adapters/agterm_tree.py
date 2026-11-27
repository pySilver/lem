"""agterm's tree, as `agtermctl tree --json` prints it: the workspaces and their sessions, each
with what Lem reads of it (the forms read in agterm's reference and its tree on 2026-11-21 and
2026-11-23).

A session's `foreground` is the argv of its main pane's program, left out while a shell holds the
pane; `realized` is false while agterm has not drawn the pane; `surfaces` name its panes, the left
one a message reaches. A session attached from another Mac names that Mac's ssh destination in
`remoteHost` and its id there in `remoteSessionID` (the second is in no reference: read in the
strings of agterm's app on 2026-11-27, beside `remoteHost` in the node's keys). Keys Lem does not
read are read past.
"""

import msgspec

from lem.adapters.agterm_ctl import TOOL
from lem.ports.faults import Unanswered
from lem.ports.terminal import Foreground, Pane


class Surface(msgspec.Struct, frozen=True, kw_only=True):
    """A pane of a session: its kind and its id."""

    kind: str = ""
    pane: str | None = msgspec.field(default=None, name="paneID")


class Node(msgspec.Struct, frozen=True, kw_only=True):
    """A session of the tree, with the id of its workspace."""

    id: str
    name: str | None = None
    cwd: str | None = None
    active: bool = False
    foreground: tuple[str, ...] | None = None
    realized: bool | None = None
    surfaces: tuple[Surface, ...] = ()
    workspace: str = ""
    remote_host: str | None = msgspec.field(default=None, name="remoteHost")
    remote_session: str | None = msgspec.field(default=None, name="remoteSessionID")

    def pane(self) -> Pane:
        """The session as the port gives it."""
        return Pane(
            id=self.id,
            name=self.name or "",
            cwd=self.cwd,
            workspace=self.workspace,
            selected=self.active,
        )

    def ground(self) -> Foreground:
        """The program in the main pane; empty for a shell, None while it is not drawn."""
        if self.foreground:
            return self.foreground
        return None if self.realized is False else ()

    def left(self) -> str:
        """The id of the left pane, which a message reaches, else `left`."""
        lefts = [one.pane for one in self.surfaces if one.kind == "left"]
        return next((pane for pane in lefts if pane), "left")


class Space(msgspec.Struct, frozen=True, kw_only=True):
    """A workspace and its sessions."""

    id: str
    sessions: tuple[Node, ...] = ()


class Tree(msgspec.Struct, frozen=True, kw_only=True):
    """The workspaces of the window agterm answered for."""

    workspaces: tuple[Space, ...] = ()


class Found(msgspec.Struct, frozen=True, kw_only=True):
    """The result of `tree --json`."""

    tree: Tree


class Answer(msgspec.Struct, frozen=True, kw_only=True):
    """`tree --json`'s answer: `{"result": {"tree": ...}}`."""

    found: Found = msgspec.field(name="result")


def nodes_of(printed: str) -> tuple[Node, ...]:
    """Every session of the tree, each with its workspace's id; `Unanswered` for an answer
    that holds no tree."""
    try:
        answer = msgspec.json.decode(printed, type=Answer)
    except msgspec.DecodeError as error:
        raise Unanswered(TOOL, f"tree --json printed no tree ({error})") from error
    spaces = answer.found.tree.workspaces
    return tuple(
        msgspec.structs.replace(node, workspace=space.id)
        for space in spaces
        for node in space.sessions
    )
