"""Which open overlay of this agterm session belongs to lem ask."""

import msgspec

from lem.adapters import agterm_ctl
from lem.board.ask.overlay_read import environment
from lem.ports.faults import Unanswered


class Overlay(msgspec.Struct, frozen=True, kw_only=True):
    """The tree's name and file of one open page."""

    id: str
    path: str | None = msgspec.field(name="file", default=None)


class Session(msgspec.Struct, frozen=True, kw_only=True):
    """The overlay slots in a session's tree."""

    id: str
    shown: tuple[Overlay, ...] = msgspec.field(name="htmlOverlays", default=())


class Space(msgspec.Struct, frozen=True, kw_only=True):
    """The sessions of an agterm workspace."""

    sessions: tuple[Session, ...] = ()


class Tree(msgspec.Struct, frozen=True, kw_only=True):
    """The agterm window's workspaces."""

    workspaces: tuple[Space, ...]


class Seen(msgspec.Struct, frozen=True, kw_only=True):
    """The tree at its place in the reply."""

    tree: Tree


class Reply(msgspec.Struct, frozen=True, kw_only=True):
    """The agtermctl response to a read of the tree."""

    answer: Seen = msgspec.field(name="result")


def read(environ: dict[str, str], session: str) -> tuple[Overlay, ...]:
    """The open overlays of this session."""
    said = agterm_ctl.said(environment(environ), "tree", "--json")
    try:
        tree = msgspec.json.decode(said, type=Reply).answer.tree
    except msgspec.DecodeError as error:
        raise Unanswered(agterm_ctl.TOOL, "the tree gave no session state") from error
    found = (node for space in tree.workspaces for node in space.sessions)
    here = next(
        (node for node in found if node.id.casefold() == session.casefold()), None
    )
    return () if here is None else here.shown
