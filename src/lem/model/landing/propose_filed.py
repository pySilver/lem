"""The refusals of `propose` for a review's finding that lost its item (`main:land.to_file`,
`settled_by_open`, `cmd_propose`): an item it was filed as, or an open item that holds it, that
a later commit removed; and an over-bar finding whose open item now says `worth: no`, which gets
an item of its own. None is lost, and none is raised again."""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from lem.model.landing.propose_facts import Facts
    from lem.records.landing.review import Filed
    from lem.records.record import Record

HELD = frozenset(("item", "same"))


def lost(record: Record, facts: Facts) -> list[Filed]:
    """The places of findings whose item is not in the tip."""
    filed = record.landing.filed if record.landing else ()
    return [
        found
        for found in filed
        if found.disposition in HELD and found.path and found.path not in facts.in_tip
    ]


def gone(record: Record, facts: Facts) -> Refusal | None:
    """An item a review's finding was filed as, or the open item that held it, removed
    after it was filed."""
    missing = lost(record, facts)
    if not missing:
        return None
    others = len(missing) - 1
    more = f", and {others} more" if others else ""
    first, slug = missing[0], record.task.slug
    return Refusal(
        "item-gone",
        f"the item {first.path} of the finding {first.finding} was removed after it was "
        f"filed{more}",
        f"a builder puts it back with lem land file {slug} --again, then this "
        "step runs again; when the owner does not want it, the item stays with `worth: no` "
        "and his reason in it, never deleted",
    )


def overs(record: Record) -> set[str]:
    """The findings a review called over the bar."""
    landing = record.landing
    reviews = landing.reviews if landing else ()
    return {
        one.id for review in reviews for one in review.findings if one.against == "over"
    }


def said_no(record: Record, facts: Facts) -> list[Filed]:
    """The places of over-bar findings held by an open item that says `worth: no` at the
    tip."""
    refused = {head.path for head in facts.heads if head.worth == "no"}
    over = overs(record)
    filed = record.landing.filed if record.landing else ()
    held = (found for found in filed if found.disposition == "same")
    return [found for found in held if found.path in refused and found.finding in over]


def refuted(record: Record, facts: Facts) -> Refusal | None:
    """An over-bar finding held by an open item that says `worth: no` at the tip: it gets an
    item of its own, `worth: later`, that names the old one, which stays."""
    found = said_no(record, facts)
    if not found:
        return None
    first, slug = found[0], record.task.slug
    return Refusal(
        "item-refuted",
        f"the finding {first.finding} is over the bar, and the open item {first.path} that "
        "holds it says `worth: no` at the tip",
        f"lem land file {slug} --again files it as an item of its own, `worth: later`, "
        "that names the old one; then this step runs again",
    )
