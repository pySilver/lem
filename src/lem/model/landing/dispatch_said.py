"""The refusals of a reply of the merge agent whose dispatch does not count
(`model/landing/dispatches.py`): one of a tip and base no brief was written for, one that names
no dispatch of its brief on record, and one that a later dispatch, or a new round, took the
place of."""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from lem.model.landing.dispatches import Pinned
    from lem.records.landing.propose import MergeDispatch

SHORT = 12


def unbriefed(slug: str, pinned: Pinned) -> Refusal:
    """The refusal of a reply of a tip and base that no brief was written for."""
    tip = pinned.tip[:SHORT]
    base = pinned.base[:SHORT]
    return Refusal(
        "brief-of",
        f"no brief of {tip} on the base {base} was written: a reply is written down with the "
        "tip and the base of the brief it answers, and it is not written down",
        f"give --tip and --base as lem land merge-review {slug} printed them with the brief",
    )


def unnamed(slug: str, pinned: Pinned) -> Refusal:
    """The refusal of a reply that names no dispatch of its brief on record."""
    which = "a dispatch" if pinned.dispatch is None else f"dispatch {pinned.dispatch}"
    tip = pinned.tip[:SHORT]
    base = pinned.base[:SHORT]
    return Refusal(
        "brief-seat",
        f"no {which} of the brief of {tip} on {base} is on record, so the record could not "
        "name the seat that read it",
        f"give --dispatch as lem land merge-review {slug} printed it with the brief; else "
        f"lem land merge-review {slug} writes the brief with its seat for a fresh agent",
    )


def stale(slug: str, named: MergeDispatch, newest: MergeDispatch | None) -> Refusal:
    """The refusal of a reply whose dispatch a later one took the place of, or that was of an
    earlier round."""
    if newest is None:
        took = "a new round of the landing started after it"
        fix = f"lem land merge-review {slug} writes the brief of this round for a fresh agent"
    else:
        number = newest.number
        took = f"dispatch {number} on `{newest.seat}` took its place"
        fix = f"the reply of dispatch {number} is written down with --dispatch {number}"
    return Refusal(
        "old-dispatch",
        f"the reply is of dispatch {named.number}, started on `{named.seat}` in round "
        f"{named.round}, and {took}: it is not written down",
        fix,
    )
