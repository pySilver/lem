"""The rows of what waits that one call of `lem waiting` lists: every task's, or one task's, with
the look of each task they name; and the groups and the breakers made from them
(`project.cmd_waiting` on `main`)."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.app.owner import briefs
from lem.model.decisions.pending import Waits, pending
from lem.model.owner import waiting

if TYPE_CHECKING:
    from collections.abc import Mapping
    from datetime import datetime

    from lem.app.owner.entries import Entry
    from lem.app.owner.looking import Looked
    from lem.model.owner.looks import Look, Row, Rows

# The group of each kind of row.
GROUPS = MappingProxyType(
    {
        "session": "no_session",
        "stopped": "stopped",
        "criteria": "criteria",
        "held": "held",
        "card": "cards",
        "after_dropped": "after_dropped",
        "blocked": "blocked",
        "plan": "plans",
        "review": "reviews",
        "merge": "pull_requests",
    }
)


@dataclass(frozen=True, kw_only=True, slots=True)
class Scope:
    """The rows listed, in the list's order, the task named (None for every task), and the
    look of every task by its name."""

    rows: Rows
    slug: str | None
    looks: Mapping[str, Look]

    def look(self, slug: str) -> Look:
        """The look of the task `slug`."""
        return self.looks[slug]


def scoped(seen: Looked, slug: str | None, now: datetime) -> Scope:
    """The rows of every task, or of the task `slug`."""
    every = waiting.rows(seen.looks, away=seen.presence.away, now=now)
    mine = tuple(row for row in every if slug in {None, row.task})
    looks = {look.record.task.slug: look for look in seen.looks}
    return Scope(rows=mine, slug=slug, looks=looks)


def grouped(scope: Scope) -> dict[str, tuple[Entry, ...]]:
    """The entries of each group, in the list's order."""
    groups: dict[str, list[Entry]] = {name: [] for name in GROUPS.values()}
    for row in scope.rows:
        group = GROUPS.get(row.kind)
        if group is not None:
            look = scope.look(row.task)
            groups[group].append(briefs.entry_of(row, look))
    return {name: tuple(groups[name]) for name in groups}


def breakers(scope: Scope) -> tuple[Waits, ...]:
    """Each breaker that waits, as `lem decisions pending` gives it: once, though it holds its
    task."""
    found = filter(is_breaker, scope.rows)
    slugs = dict.fromkeys(row.task for row in found)
    named = tuple(scope.look(slug).record.task for slug in slugs)
    return pending(named, named=False).waiting


def is_breaker(row: Row) -> bool:
    """Whether the row is a breaker's."""
    return row.kind == "breaker"
