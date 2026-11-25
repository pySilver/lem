"""The waits of the workspace, with the session that can receive their answers."""

from typing import TYPE_CHECKING

from lem.model.owner import merging, need, waiting
from lem.records.base import Frozen
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.app.owner.looking import Looked

from lem.addons.inbox.records import Wait
from lem.model.owner.looks import Look, Row
from lem.records.base import Moment

OWN_NOTE = frozenset(("session", "stopped", "after_dropped"))
BOARD_ONLY = frozenset(("review", "card"))
type Live = dict[str, str]
type Facts = tuple[RowFacts, ...]


class RowFacts(Frozen, frozen=True, kw_only=True):
    """One owner's wait and the board facts needed to describe it."""

    row: Row
    look: Look
    claude: str | None
    now: Moment

    @classmethod
    def of(cls, row: Row, seen: dict[str, Look], live: Live, now: Moment) -> RowFacts:
        """Read a row beside its task and the task's current Claude Code id."""
        slug = row.task
        claude = live.get(slug)
        return cls(row=row, look=seen[slug], claude=claude, now=now)


def facts(looked: Looked, live: Live, now: Moment) -> Facts:
    """Group card and merge-review rows with the places that already answer them."""
    present = waiting.rows(looked.looks, away=looked.presence.away, now=now)
    by_task = {look.record.task.slug: look for look in looked.looks}
    eligible = eligible_rows(present)
    return tuple(RowFacts.of(row, by_task, live, now) for row in eligible)


def eligible_rows(present: tuple[Row, ...]) -> tuple[Row, ...]:
    """One session note stands for any other waits of that task."""
    session_kinds = {"session", "stopped"}
    missing = {row.task for row in present if row.kind in session_kinds}
    board_rows = (row for row in present if row.kind not in BOARD_ONLY)
    return tuple(
        row
        for row in board_rows
        if row.task not in missing or row.kind in session_kinds
    )


def wait_of(found: RowFacts) -> Wait | None:
    """A live session answers. A note explains when the owner must use the board."""
    row = found.row
    asks = row.kind not in OWN_NOTE and not row.say and merge_ok(found)
    if asks and still_opening(found):
        return None
    return Wait(
        key=row.key,
        task=row.task,
        kind=row.kind,
        since=row.since,
        asks=asks,
        session=found.claude if asks else None,
        tip=tip_of(found),
    )


def still_opening(found: RowFacts) -> bool:
    """Wait for the hook that names the live session."""
    session = found.look.session
    if session is None or not session.live or found.claude:
        return False
    return found.now - session.since < need.GRACE


def merge_ok(found: RowFacts) -> bool:
    """The owner's merge question must refer to the same reviewed proposal."""
    if found.row.kind != "merge":
        return True
    if found.row.conflict:
        return False
    landing = found.look.record.landing or Landing()
    review = merging.calling(found.look.record)
    return bool(
        landing.proposed
        and not landing.refused
        and review
        and review.tip == landing.proposed.tip
    )


def tip_of(found: RowFacts) -> str | None:
    """Bind any message about a merge to its full proposed tip."""
    landing = found.look.record.landing
    if found.row.kind == "merge" and landing and landing.proposed:
        return landing.proposed.tip
    return None
