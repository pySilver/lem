"""What the watcher of the board's notifications reads: each workspace's list of what waits for
the owner, what is new on it since the last look, and the one push that tells of it
(`push.Watcher.look` on `main`).

The push names the first new row's verb and its task's page, with how many more came; a
workspace of example tasks (its state folder's mark `demo`) is not read.
"""

from itertools import chain
from typing import TYPE_CHECKING

from lem.app.owner.looking import looked
from lem.app.sessions.here import bound
from lem.board import workspaces
from lem.board.push.news import gained
from lem.kernel import clock
from lem.model.owner import waiting

if TYPE_CHECKING:
    from pathlib import Path

    from lem.adapters.notify_push_devices import Memory
    from lem.app.owner.looking import Looked
    from lem.store.places import Workspace

DEMO = "demo"

type Found = tuple[str, Looked]
type New = tuple[str, Looked, waiting.Row]
type Seen = dict[str, Memory]


def every(home: Path, host: str) -> list[Found]:
    """Each workspace of the list with its look now, but those of example tasks."""
    found: list[Found] = []
    for name, _ in workspaces.named(workspaces.listed(home), host):
        space = shown(home, host, name)
        if space is not None:
            found.append((name, look_at(space)))
    return found


def shown(home: Path, host: str, name: str) -> Workspace | None:
    """The workspace of the name, None when it is gone or holds example tasks."""
    space = workspaces.found(home, host, name)
    if space is None or (space.state / DEMO).is_file():
        return None
    return space


def look_at(space: Workspace) -> Looked:
    """The look at the workspace now."""
    here = bound(space.checkout)
    return looked(here, clock.now())


def rows_of(found: Looked) -> waiting.Rows:
    """The workspace's rows of what waits for the owner now."""
    moment = clock.now()
    return waiting.rows(found.looks, away=found.presence.away, now=moment)


def news_in(seen: Seen, name: str, found: Looked, now: float) -> list[New]:
    """The new rows of one workspace, in its order; `seen` takes its list's memory."""
    rows = rows_of(found)
    keys = [row.key for row in rows]
    fresh, memory = gained(seen.get(name), keys, now)
    seen[name] = memory
    kept = [row for row in rows if row.key in fresh]
    return [(name, found, row) for row in kept]


def news_of(seen: Seen, found: list[Found], now: float) -> list[New]:
    """The new rows of every workspace, in the list's order; `seen` takes each memory."""
    each = [news_in(seen, name, one, now) for name, one in found]
    return list(chain.from_iterable(each))
