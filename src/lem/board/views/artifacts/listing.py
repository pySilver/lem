"""A task's files on the map, from what the gather listed of its folder (`artifacts.files`,
`pictures_named` and `board_task.artifact_map` on `main`): each file but a hidden one and a lock,
the plan first in its section while the task's worktree holds it, and the pictures each of its
documents names.

`count` is the number of documents the tab bar shows beside Artifacts.
"""

from typing import TYPE_CHECKING

from lem.board.views.artifacts.arrange import arrange
from lem.board.views.artifacts.kinds import MARKDOWN, kind_of
from lem.board.views.artifacts.mapped import Entry
from lem.board.views.artifacts.pictures import shows_of
from lem.board.views.artifacts.scratch import place
from lem.board.views.artifacts.spots import DOCS, GROUPS, PLAN, PR_DOC, Spot

if TYPE_CHECKING:
    from lem.board.views.artifacts.mapped import Map
    from lem.board.views.world import Seen

THE_PLAN = Spot(group=PLAN, title="The plan")


def listed(path: str) -> bool:
    """Whether a file of the folder is on the map: no hidden file and no lock."""
    hidden = any(part.startswith(".") for part in path.split("/"))
    return not hidden and not path.endswith(".lock")


def entries_of(seen: Seen) -> tuple[Entry, ...]:
    """The task's files in the map's order: by section, the plan first, then by path."""
    landing = seen.record.landing
    proposed = landing.proposed if landing else None
    confirmed = proposed.text if proposed else None
    found = [entry_of(path, confirmed) for path in seen.files if listed(path)]
    if seen.plan_file is not None:
        found.append(plan_of(seen.plan_file.stat.path))
    return tuple(sorted(found, key=order))


def plan_of(path: str) -> Entry:
    """The task's plan in its worktree, first in its section."""
    return Entry(path=path, spot=THE_PLAN, kind=MARKDOWN, first=True)


def entry_of(path: str, confirmed: str | None) -> Entry:
    """A file of the folder, placed on the map."""
    spot = DOCS[PR_DOC] if path == confirmed else place(path)
    return Entry(path=path, spot=spot, kind=kind_of(path))


def order(entry: Entry) -> tuple[int, bool, str]:
    """An entry's place in the map's order: its section, the plan first, its path."""
    return GROUPS.index(entry.spot.group), not entry.first, entry.path


def map_of(seen: Seen) -> Map:
    """The task's files on the map of every task."""
    entries = entries_of(seen)
    return arrange(entries, shows_of(seen, entries))


def count(seen: Seen) -> int:
    """The number of documents on the task's map."""
    return map_of(seen).count
