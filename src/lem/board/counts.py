"""The workspaces of the machine's list as `GET /api/workspaces` gives them: each one's name, path
and address, how many tasks wait for the owner, how many build and how many are in their checks
and review (`Workspace.count` and `Machine.listing` on `main`).

What waits is the board's "Waits for you", its rows grouped by task (`waiting.stacks`). A
workspace's counts are read again at most once in FRESH seconds, but the one a page shows, which
is counted at its request, so that the page's switcher says what its sidebar says. A workspace
whose files do not read has no counts and says why; the others still show.
"""

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import msgspec

from lem.board import count_look, workspaces
from lem.kernel import clock, errors
from lem.model.owner import waiting
from lem.records.workspace import Row

if TYPE_CHECKING:
    from pathlib import Path

    from lem.app.owner.looking import Looked
    from lem.store.places import Workspace

# How long a workspace's counts are kept, in seconds (`serve.REFRESH_SECONDS` on `main`).
FRESH = 5.0
FAILED = (errors.Refusal, errors.Fault, OSError, ValueError)


class Count(msgspec.Struct, frozen=True, kw_only=True, omit_defaults=True):
    """How many tasks of a workspace wait for the owner, build, are in their checks, and
    run (the two together); or why none is known."""

    waits: int | None = None
    building: int | None = None
    checks: int | None = None
    running: int | None = None
    problem: str | None = None


def counted(space: Workspace, home: Path) -> Count:
    """The counts of the workspace now."""
    try:
        seen = count_look.looked(space, home)
    except FAILED as error:
        return Count(problem=str(error))
    return count_of(seen)


def count_of(seen: Looked) -> Count:
    """The counts of a look at a workspace."""
    statuses = [one.record.task.status for one in seen.looks]
    away = seen.presence.away
    rows = waiting.rows(seen.looks, away=away, now=clock.now())
    building = statuses.count("building")
    checks = statuses.count("landing")
    return Count(
        waits=len(waiting.stacks(rows)),
        building=building,
        checks=checks,
        running=building + checks,
    )


@dataclass
class Counts:
    """Each workspace's counts, with when they were read."""

    kept: dict[str, tuple[float, Count]] = field(default_factory=dict)

    def of(self, space: Workspace, home: Path, *, fresh: bool) -> Count:
        """The counts of the workspace, read again when `fresh` or older than FRESH."""
        key = str(space.checkout)
        known = self.kept.get(key)
        now = time.monotonic()
        if fresh or known is None or now - known[0] >= FRESH:
            known = (now, counted(space, home))
            self.kept[key] = known
        return known[1]

    def rows(
        self, home: Path, host: str, fresh: str = "", current: Row | None = None
    ) -> Rows:
        """Each workspace of the list whose checkout still has Lem set up, the one named
        `fresh` counted now."""
        named = workspaces.named(workspaces.listed(home), host)
        found: list[Row] = []
        for name, checkout in named:
            if current is not None and (name, checkout) == (current.name, current.path):
                found.append(current)
                continue
            space = workspaces.found(home, host, name)
            if space is not None:
                found.append(self.row(space, name, host, home, fresh=fresh))
        return tuple(found)

    def row(
        self, space: Workspace, name: str, host: str, home: Path, *, fresh: str
    ) -> Row:
        """The row of the workspace named `name`."""
        count = self.of(space, home, fresh=name == fresh)
        fields = msgspec.structs.asdict(count)
        path = str(space.checkout)
        address = f"/{host}/{name}/"
        return Row(name=name, path=path, url=address, host=host, **fields)


type Rows = tuple[Row, ...]
