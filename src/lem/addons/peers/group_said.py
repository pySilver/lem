"""What the board says after this Mac's agterm showed a joined machine's session: the line, and a
notice when the group is not whole (agterm be92bc63, `ControlServer+RemoteGroup.swift`).

agterm keeps the rows of a group attach that failed for a companion, and its reply names what
failed; a far agterm too old to name a session's companions gives `membershipKnown: false`, and a
companion may then be missing with no word of it.
"""

from typing import TYPE_CHECKING

from lem.records.base import Frozen

if TYPE_CHECKING:
    from lem.adapters.agterm_group_forms import Group, Reply

SWITCHED = "Switched to the session."


class Shown(Frozen, frozen=True, kw_only=True):
    """The line the board says, and what the owner must know beside it."""

    said: str
    notice: str | None = None


def missing_of(group: Group | None) -> str:
    """The far ids of the companions agterm did not attach, or where to read them."""
    gone = (
        [member.origin for member in group.companions if not member.id] if group else []
    )
    return ", ".join(gone) or "agterm's words name them"


def kept_line(error: str, missing: str) -> str:
    """The notice of a group attach that kept the session and only part of its companions."""
    return (
        f"agterm kept the session with only part of its companions ({error}). Not "
        f"attached: {missing}. File, Attach Remote in agterm attaches a companion alone."
    )


def notice_of(peer: str, reply: Reply) -> str | None:
    """What the attach left out, or None for a whole group."""
    group = reply.found.group if reply.found else None
    lines = []
    if not reply.ok:
        lines.append(kept_line(reply.error or "", missing_of(group)))
    if group is not None and not group.known:
        lines.append(
            f"The agterm on {peer} does not say which companions the session has, so one "
            "can be missing here."
        )
    return " ".join(lines) or None


def opened(peer: str, reply: Reply) -> Shown:
    """The line and the notice of a session attached here."""
    return Shown(
        said=f"Opened the session of {peer} on this Mac.", notice=notice_of(peer, reply)
    )
