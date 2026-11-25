"""What the terminal shows of the sessions now, read once for a command: each session by its id
in capitals, the program in its main pane, and whether a session still carries its task (an
agent runs in it, the terminal does not know yet, or it opened under a minute ago:
`agents.live`)."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from lem.app.sessions import agents, beside
from lem.kernel.errors import Refusal
from lem.ports.terminal import Pane, Unreadable

if TYPE_CHECKING:
    from datetime import datetime

    from lem.app.sessions.acts import Open
    from lem.app.sessions.here import Here


@dataclass(frozen=True, kw_only=True, slots=True)
class Seen:
    """The terminal's sessions and their main panes' programs, by id in capitals."""

    panes: dict[str, Pane]
    grounds: dict[str, beside.Foreground]

    def pane(self, session: str) -> Pane | None:
        """The session `session`, when the terminal lists it."""
        return self.panes.get(session.upper())

    def ground(self, session: str) -> beside.Foreground:
        """The program in the session's main pane, None when it is not known."""
        return self.grounds.get(session.upper())

    def carries(self, opened: Open | None, now: datetime) -> Pane | None:
        """The pane of the session `opened` while it still carries its task, else None."""
        pane = self.pane(opened.session) if opened else None
        if opened is None or pane is None:
            return None
        ground = self.ground(opened.session)
        alive = agents.live(ground, listed=True, opened=opened.at, now=now)
        return pane if alive else None


def listed(here: Here) -> dict[str, Pane]:
    """The terminal's sessions by id in capitals; refused when the terminal cannot say."""
    panes = here.ports.terminal.sessions()
    if isinstance(panes, Unreadable):
        raise Refusal(
            "terminal",
            f"agterm's sessions could not be read: {panes.why}",
            "the owner checks that agterm runs (lem doctor), then runs this again",
        )
    return {pane.id.upper(): pane for pane in panes}


def look(here: Here) -> Seen:
    """The terminal's sessions and their programs, now."""
    found = beside.looks(here.ports.terminal).foregrounds()
    grounds = {key.upper(): words for key, words in found.items()}
    return Seen(panes=listed(here), grounds=grounds)
