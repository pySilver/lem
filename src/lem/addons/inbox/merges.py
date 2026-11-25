"""The proposal, refusal and review an Inbox merge message is about."""

from typing import TYPE_CHECKING

import msgspec

from lem.kernel.files import digest
from lem.model.owner import merging

if TYPE_CHECKING:
    from lem.addons.inbox.source import RowFacts
    from lem.records.landing.merge import Refused
    from lem.records.landing.propose import MergeRead


def tip_of(found: RowFacts) -> str | None:
    """Bind any message about a merge to its full proposed tip."""
    landing = found.look.record.landing
    if found.row.kind == "merge" and landing and landing.proposed:
        return landing.proposed.tip
    return None


def refusal_of(found: RowFacts) -> Refused | None:
    """Only a refusal of the proposal in view holds its merge."""
    landing = found.look.record.landing
    refused = landing.refused if landing else None
    return refused if refused and refused.tip == tip_of(found) else None


def review_of(found: RowFacts) -> MergeRead | None:
    """The Inbox asks only for a reviewed proposal that the owner can merge."""
    if not tip_of(found) or found.row.conflict or refusal_of(found):
        return None
    return merging.calling(found.look)


def identity(review: MergeRead | None) -> str | None:
    """A new review can change the question without a new proposed tip."""
    return digest(msgspec.json.encode(review)) if review else None
