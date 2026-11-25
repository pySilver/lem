"""What every record of Lem shares: frozen msgspec structs, keyword fields, defaults left out of
the JSON, and unknown keys read past.

A record is a value: a change makes a new one (`msgspec.structs.replace`). Unknown keys are read
past, so that a release reads a record that the next release wrote with a key beside the old ones
(AGENTS.md, "a change of the form of a record takes two releases"). A moment is a UTC `datetime`,
written `2026-11-24T10:18:18Z`, and one with no zone is refused; a commit is its full sha, 40
lower-case hex characters.
"""

from datetime import date, datetime
from typing import Annotated

import msgspec

# A moment with its zone, so that two compare; a decoded time with none is refused.
type Moment = Annotated[datetime, msgspec.Meta(tz=True)]
type Day = date
# A full commit id, as `land.record_tip_refusal` on `main` holds it; an abbreviation is refused.
type Sha = Annotated[str, msgspec.Meta(pattern="^[0-9a-f]{40}$")]
type Slug = str
# A path inside the task's folder, as the record cites it: `reviews/review-2.json`.
type TaskPath = str


class Frozen(msgspec.Struct, frozen=True, kw_only=True, omit_defaults=True):
    """The base of every record: frozen, keyword fields, defaults left out of the JSON."""


class Tagged(Frozen, tag_field="kind", frozen=True, kw_only=True):
    """The base of each member of a union, told apart by its `kind`."""
