"""What the watcher of the board's notifications reads: each workspace's list of what waits for
the owner, what is new on it since the last look, and the one push that tells of it
(`push.Watcher.look` on `main`).

The push names the first new row's verb and its task's page, with how many more came; a
workspace of example tasks (its state folder's mark `demo`) is not read.
"""

import sys
from typing import TYPE_CHECKING, NamedTuple

from lem.app.owner.looking import looked
from lem.app.sessions.here import bound
from lem.board import workspaces
from lem.board.push.news import gained
from lem.kernel import clock, errors
from lem.model.owner import waiting

if TYPE_CHECKING:
    from pathlib import Path

    from lem.adapters.notify_push_devices import Memory
    from lem.app.owner.looking import Looked

DEMO = "demo"
FAILED = (errors.Refusal, errors.Fault, OSError, ValueError)

type New = tuple[str, Looked, waiting.Row]
type Seen = dict[str, Memory]


class Found(NamedTuple):
    """A workspace's display name, checkout path, and look at its tasks."""

    name: str
    path: str
    look: Looked


def every(home: Path, host: str) -> list[Found]:
    """Each workspace of the list with its look now, but those of example tasks."""
    found: list[Found] = []
    for name, _ in workspaces.named(workspaces.listed(home), host):
        try:
            one = shown(home, host, name)
        except FAILED as error:
            sys.stderr.write(f"the board's notifications skip {name}: {error}\n")
            continue
        if one is not None:
            found.append(one)
    return found


def shown(home: Path, host: str, name: str) -> Found | None:
    """The workspace of the name, None when it is gone or holds example tasks."""
    space = workspaces.found(home, host, name)
    if space is None or (space.state / DEMO).is_file():
        return None
    look = looked(bound(space.checkout), clock.now())
    return Found(name, str(space.checkout), look)


def rows_of(found: Looked) -> waiting.Rows:
    """The workspace's rows of what waits for the owner now."""
    moment = clock.now()
    return waiting.rows(found.looks, away=found.presence.away, now=moment)


def news_in(seen: Seen, found: Found, now: float) -> list[New]:
    """The new rows of one workspace, in its order; `seen` takes its list's memory."""
    rows = rows_of(found.look)
    keys = [row.key for row in rows]
    fresh, memory = gained(seen.get(found.path), keys, now)
    seen[found.path] = memory
    return [(found.name, found.look, row) for row in rows if row.key in fresh]


def news_of(seen: Seen, found: list[Found], now: float) -> list[New]:
    """The new rows of every workspace, in the list's order; `seen` takes each memory."""
    news: list[New] = []
    for one in found:
        news.extend(news_in(seen, one, now))
    return news
