"""Whether the pane still runs the task's current session with an agent."""

from typing import TYPE_CHECKING

from lem.app.owner.sessions import agent_is_live
from lem.app.sessions import agents, log
from lem.app.wiring import bound
from lem.kernel import paths
from lem.ports.place import Place

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path


def current(folder: Path, session: str, environ: Mapping[str, str]) -> bool:
    """Match the newest session on record and check its pane's agent."""
    return log.same(newest(folder), session) and running(folder, session, environ)


def newest(folder: Path) -> str | None:
    """The session Lem opened most recently for this task."""
    opened = log.newest_open(log.read(folder))
    return None if opened is None else opened.session


def running(folder: Path, session: str, environ: Mapping[str, str]) -> bool:
    """Whether this session's pane has a running agent."""
    place = Place(
        checkout=folder.parents[3],
        home=paths.home(environ),
        environ=environ,
    )
    grounds = bound(place).terminal.foregrounds()
    for pane, words in grounds.items():
        if log.same(pane, session):
            return agent_is_live(listed=True, agent=agents.agent_runs(words))
    return False
