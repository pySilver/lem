"""Each start of the merge agent, and the reply that counts from one alone (`landing.md` C, "In
`open`").

A start is a dispatch on the task's record: its number, the tip, base and round of its brief,
and the seat it was started on. The step that writes a brief again for the same tip, base, round
and seat repeats the dispatch, with its number and its brief; another seat (a stand-in, an edit
of the settings) or a new round is a new dispatch, which takes the place of the one before for
that tip and base. A reply names its dispatch, and counts only while that dispatch is the newest
of its brief's tip and base in the landing's round: the answer of an agent started earlier
records nothing, whatever seat the settings name by then.
"""

from typing import TYPE_CHECKING

from lem.model.landing import dispatch_said
from lem.records.base import Frozen, Moment, Sha
from lem.records.landing.propose import MergeDispatch
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.kernel.errors import Refusal
    from lem.records.record import Record

# A brief by the first twelve characters of its tip and base, its round and its dispatch.
BRIEF = "merge-brief-{0:.12}-{1:.12}-{2}-{3}.md"


class Pinned(Frozen, frozen=True, kw_only=True):
    """What a reply names of the start it answers: the tip and base of its brief, and the
    dispatch's number, as `lem land merge-review` printed them."""

    tip: Sha
    base: Sha
    dispatch: int | None


def current(landing: Landing, tip: str, base: str) -> MergeDispatch | None:
    """The newest dispatch of `tip` on `base` in the landing's round, or None."""
    found = [
        one
        for one in landing.dispatches
        if (one.tip, one.base, one.round) == (tip, base, landing.round)
    ]
    return found[-1] if found else None


def repeated(landing: Landing, tip: str, base: str, seat: str) -> MergeDispatch | None:
    """The dispatch that a new start of `seat` on the brief of `tip` on `base` repeats: the
    current one, when it was started on that seat."""
    found = current(landing, tip, base)
    return found if found is not None and found.seat == seat else None


def started(landing: Landing, read: tuple[str, str, str], now: Moment) -> MergeDispatch:
    """The start of the merge agent on the seat of `read` (its tip, base and seat): the
    current dispatch again when it is on that seat, else a new one with a brief of its own."""
    tip, base, seat = read
    found = repeated(landing, tip, base, seat)
    if found is not None:
        return found
    # One past every dispatch of the landing, of any round, so that no two starts share one.
    number = len(landing.dispatches) + 1
    return MergeDispatch(
        number=number,
        tip=tip,
        base=base,
        round=landing.round,
        seat=seat,
        brief=BRIEF.format(tip, base, landing.round, number),
        at=now,
    )


def named_by(landing: Landing, pinned: Pinned) -> MergeDispatch | None:
    """The dispatch on record that a reply names, of the tip and base it names."""
    wanted = (pinned.dispatch, pinned.tip, pinned.base)
    found = (
        one for one in landing.dispatches if (one.number, one.tip, one.base) == wanted
    )
    return next(found, None)


def unknown(landing: Landing, slug: str, pinned: Pinned) -> Refusal:
    """The refusal of a reply that names no dispatch on record: no brief of its tip and base
    was written, or none of their dispatches has its number."""
    briefs = {(one.tip, one.base) for one in landing.dispatches}
    known = (pinned.tip, pinned.base) in briefs
    said = dispatch_said.unnamed if known else dispatch_said.unbriefed
    return said(slug, pinned)


def resolved(record: Record, pinned: Pinned) -> MergeDispatch | Refusal:
    """The dispatch a reply answers, or why it is refused: no brief of its tip and base was
    written, or it names no dispatch of them, or one that a later dispatch of the proposed tip
    took the place of. A dispatch of another tip than the proposed one is the step's to refuse
    (`old-tip`)."""
    landing = record.landing or Landing()
    named = named_by(landing, pinned)
    if named is None:
        return unknown(landing, record.task.slug, pinned)
    proposed = landing.proposed.tip if landing.proposed else None
    newest = current(landing, named.tip, named.base)
    if named.tip == proposed and newest != named:
        return dispatch_said.stale(record.task.slug, named, newest)
    return named
