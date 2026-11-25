"""The sessions of agterm for the `Terminal` port on agterm (`terminal_agterm`): the list, a close,
a line, a mark, a name, and what the tree says of each session's main pane and mailbox.

A list agterm does not give is `Unreadable`, never an empty list; any other call it refuses is
`Unanswered`. A session is found by its id in no regard to case, as agterm prints ids in capitals
and a pane's environment may hold them in either.
"""

from typing import TYPE_CHECKING

from lem.adapters.agterm_ctl import TOOL, said
from lem.adapters.agterm_tree import Foreground, Node, nodes_of
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


class AgtermSessions:
    """The sessions: list, close, a line to one, its mark, its name."""

    def __init__(self, environ: Mapping[str, str]) -> None:
        """Keep the environment the command started with: its PATH, socket and window."""
        self.environ = environ

    def nodes(self) -> tuple[Node, ...]:
        """Every session of the tree."""
        return nodes_of(said(self.environ, *TREE))

    def node(self, session: str) -> Node:
        """The session `session`, or `Unanswered` for one that is gone."""
        wanted = session.upper()
        found = (node for node in self.nodes() if node.id.upper() == wanted)
        known = next(found, None)
        if known is None:
            raise Unanswered(TOOL, f"no session {session}")
        return known

    def sessions(self) -> tuple[Pane, ...] | Unreadable:
        """Every session of agterm, or why it could not be read."""
        try:
            nodes = self.nodes()
        except Unanswered as unanswered:
            return Unreadable(why=unanswered.said)
        return tuple(node.pane() for node in nodes)

    def close(self, session: str, *, when_unselected: bool) -> None:
        """Close the session with agterm's undo, but one the owner looks at when told so."""
        node = self.node(session)
        if when_unselected and node.active:
            return
        said(self.environ, SESSION, "close", TARGET, node.id, "--undoable")

    def tell(self, session: str, line: str) -> None:
        """Send `line` to the session's left pane, as mail that waits for its turn's end."""
        target = self.node(session).id
        pane = f"{target}:left"
        said(self.environ, "msg", "send", line, "--to", pane, window=False)

    def mark(self, session: str, status: Mark) -> None:
        """Set the session's glyph in agterm's sidebar."""
        target = self.node(session).id
        glyph = dict(GLYPHS)[status]
        said(self.environ, SESSION, "status", glyph, TARGET, target)


class AgtermLooks(AgtermSessions):
    """What the tree says of each session beside the port's list: the program in its main
    pane, and a line still in its mailbox."""

    def foregrounds(self) -> dict[str, Foreground]:
        """Each session's foreground: the words of the program in its main pane, empty for
        a shell that holds it, None while agterm has not drawn the pane."""
        return {node.id: node.ground() for node in self.nodes()}

    def waiting(self, session: str, line: str) -> bool:
        """Whether `line` still waits in the mailbox of the session's left pane: `msg read`,
        which removes nothing."""
        node = self.node(session)
        pane = f"{node.id}:{node.left()}"
        printed = said(
            self.environ, "msg", "read", "--as", pane, "--json", window=False
        )
        return line in printed

    def rename(self, session: str, name: str) -> None:
        """Name the session `name` in agterm's sidebar."""
        target = self.node(session).id
        said(self.environ, SESSION, "rename", name, TARGET, target)
