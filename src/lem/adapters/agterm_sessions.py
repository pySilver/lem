"""The sessions of agterm for the `Terminal` port on agterm (`terminal_agterm`): the list, a close,
a line, a mark, a name, and what the tree says of each session's main pane and mailbox.

A list agterm does not give is `Unreadable`, never an empty list; any other call it refuses is
`Unanswered`. A session is found by its id in no regard to case, as agterm prints ids in capitals
and a pane's environment may hold them in either.
"""

from typing import TYPE_CHECKING

from lem.adapters.agterm_ctl import TOOL, Node, nodes_of, pane_of, said
from lem.ports.faults import Unanswered
from lem.ports.terminal import Mark, Pane, Unreadable

if TYPE_CHECKING:
    from collections.abc import Mapping

SESSION = "session"
TARGET = "--target"
TREE = ("tree", "--json")
# agterm's status glyph for each mark of the port (`session status`).
GLYPHS = (
    ("working", "active"),
    ("waiting", "blocked"),
    ("done", "completed"),
    ("stopped", "blocked"),
    ("none", "idle"),
)

type Foreground = tuple[str, ...] | None


class AgtermSessions:
    """The sessions: list, close, a line to one, its mark, its name."""

    def __init__(self, environ: Mapping[str, str]) -> None:
        """Keep the environment the command started with: its PATH, socket and window."""
        self.environ = environ

    def node(self, session: str) -> Node:
        """The tree's node of the session `session`, or `Unanswered` for one that is gone."""
        nodes = nodes_of(said(self.environ, *TREE))
        wanted = session.upper()
        found = next((node for node in nodes if str(node["id"]).upper() == wanted), None)
        if found is None:
            raise Unanswered(TOOL, f"no session {session}")
        return found

    def sessions(self) -> tuple[Pane, ...] | Unreadable:
        """Every session of agterm, or why it could not be read."""
        try:
            return tuple(pane_of(node) for node in nodes_of(said(self.environ, *TREE)))
        except Unanswered as unanswered:
            return Unreadable(why=unanswered.said)

    def close(self, session: str, *, when_unselected: bool) -> None:
        """Close the session with agterm's undo, but one the owner looks at when told so."""
        if when_unselected and self.node(session).get("active"):
            return
        target = str(self.node(session)["id"])
        said(self.environ, SESSION, "close", TARGET, target, "--undoable")

    def tell(self, session: str, line: str) -> None:
        """Send `line` to the session's left pane, as mail that waits for its turn's end."""
        target = str(self.node(session)["id"])
        said(self.environ, "msg", "send", line, "--to", f"{target}:left", window=False)

    def mark(self, session: str, status: Mark) -> None:
        """Set the session's glyph in agterm's sidebar."""
        target = str(self.node(session)["id"])
        glyph = dict(GLYPHS)[status]
        said(self.environ, SESSION, "status", glyph, TARGET, target)

    def rename(self, session: str, name: str) -> None:
        """Name the session `name` in agterm's sidebar."""
        target = str(self.node(session)["id"])
        said(self.environ, SESSION, "rename", name, TARGET, target)


class AgtermLooks(AgtermSessions):
    """What the tree says of each session beside the port's list: the program in its main
    pane, and a line still in its mailbox."""

    def foregrounds(self) -> dict[str, Foreground]:
        """Each session's foreground: the words of the program in its main pane, empty for
        a shell that holds it, None while agterm has not drawn the pane (`realized`)."""
        nodes = nodes_of(said(self.environ, *TREE))
        return {str(node["id"]): foreground_of(node) for node in nodes}

    def waiting(self, session: str, line: str) -> bool:
        """Whether `line` still waits in the mailbox of the session's left pane: `msg read`,
        which removes nothing."""
        node = self.node(session)
        pane = f"{node['id']}:{left_pane(node)}"
        return line in said(self.environ, "msg", "read", "--as", pane, "--json", window=False)


def foreground_of(node: Node) -> Foreground:
    """The words of a node's `foreground` (the argv of its main pane's program), empty when a
    shell holds the pane, None while agterm has not drawn it."""
    ground = node.get("foreground")
    if isinstance(ground, list) and ground:
        return tuple(str(word) for word in ground)
    return None if node.get("realized") is False else ()


def left_pane(node: Node) -> str:
    """The id of the session's left pane, which a message reaches, else `left`."""
    surfaces = node.get("surfaces")
    found = (
        str(surface["paneID"])
        for surface in (surfaces if isinstance(surfaces, list) else ())
        if isinstance(surface, dict)
        and surface.get("kind") == "left"
        and surface.get("paneID")
    )
    return next(found, "left")
