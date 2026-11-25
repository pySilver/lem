"""The tab Criteria and decisions of a task (`board_task.criteria_tab` on `main`): while the
criteria wait for the owner's yes, that card first; the plan's How it works; the card of the
criteria (its line, the rows of their read, approval and changes, the criteria); and the card of
the decisions. A card of a task that ended with nothing in it is not drawn, and a tab with
neither says so; a pruned task says what went with its journal."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.board.inputs.task.decisions import Criteria
from lem.board.views.artifacts.documents import document
from lem.board.views.checks.went import pruned, went
from lem.board.views.criteria import approved, heads, ordered
from lem.board.views.criteria.approve import approve
from lem.board.views.criteria.listed import criteria_rows
from lem.board.views.criteria.terms import track_words

if TYPE_CHECKING:
    from lem.board.inputs.parts import Document
    from lem.board.views.world import Seen, World

ENDED = frozenset(("landed", "answered", "dropped"))
NO_CRITERIA = "The agent writes the acceptance criteria at the top of the plan"
NO_DECISION = (
    "Each decision the build takes, and each breaker that stops it, comes here"
)
NEITHER = "The task ended with no criteria and no decision on record"


def said_of(seen: Seen) -> str | None:
    """The line of the card of the criteria: their track and why."""
    criteria = seen.record.task.criteria
    stated = criteria.approvals[-1] if criteria.approvals else None
    if criteria.size is None:
        criteria = stated
    if criteria is None or not criteria.size or not criteria.why:
        return None
    track = track_words(criteria.size)
    return f"{track}, because {criteria.why}"


def how_of(seen: Seen) -> Document | None:
    """The plan's How it works, its sentences and its chart, or None."""
    how = seen.record.task.criteria.how
    slug = seen.record.task.slug
    return document(f"how-{slug}", how) if how else None


def criteria(world: World, seen: Seen) -> Criteria:
    """The tab Criteria and decisions of the task `seen`."""
    if pruned(seen):
        return Criteria(went=went(world, seen, "criteria"))
    found = (heads.read_row(world, seen), approved.approval_row(world, seen))
    reads = tuple(row for row in found if row is not None)
    reads += approved.change_rows(world, seen)
    rows = criteria_rows(seen.record)
    tab = decided(world, seen)
    if seen.record.task.status in ENDED and not (reads or rows):
        return tab if tab.ended else replace(tab, how=how_of(seen))
    return replace(
        tab,
        ended=None,
        approve=approve(world, seen),
        how=how_of(seen),
        criteria_said=said_of(seen),
        reads=reads,
        criteria=rows,
        criteria_empty=None if reads or rows else NO_CRITERIA,
    )


def decided(world: World, seen: Seen) -> Criteria:
    """The card of the decisions alone; a task that ended with none has neither card."""
    shown = ordered.decisions(world, seen)
    orphans = ordered.orphans(world, seen)
    if seen.record.task.status in ENDED and not (shown or orphans):
        return Criteria(ended=NEITHER)
    return Criteria(
        decisions_said=ordered.said_of(seen),
        decisions=shown,
        orphans=orphans,
        decisions_empty=None if shown or orphans else NO_DECISION,
    )
