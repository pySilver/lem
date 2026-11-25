"""What the board can say of an approval or a merge call on record."""

from typing import TYPE_CHECKING

from lem.model.landing import merge_standing

if TYPE_CHECKING:
    from lem.records.landing.propose import Standing
    from lem.records.record import Record


def standing(record: Record) -> Standing | None:
    """The approval that still stands after the forge's last answer for this tip."""
    landing = record.landing
    if landing is None or landing.proposed is None or landing.intent is not None:
        return None
    refused = landing.refused
    if refused and refused.source == "github" and refused.tip == landing.proposed.tip:
        return None
    return merge_standing.standing_of(record)


def uncertain(record: Record) -> str | None:
    """What the owner sees when the forge has not answered a merge call."""
    landing = record.landing
    if landing is None or landing.intent is None:
        return None
    said = "The merge outcome is uncertain. Check the pull request on GitHub."
    if landing.pull is None:
        return said
    url = landing.pull.url
    return f"{said} {url}"
