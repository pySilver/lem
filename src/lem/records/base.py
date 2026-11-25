"""What every record of Lem shares: frozen msgspec structs, keyword fields, defaults left out of
the JSON, and unknown keys read past.

A record is a value: a change makes a new one (`msgspec.structs.replace`). Unknown keys are read
past, so that a release reads a record that the next release wrote with a key beside the old ones
(AGENTS.md, "a change of the form of a record takes two releases"). A moment is a UTC `datetime`,
written `2026-11-24T10:18:18Z`; a commit is its full sha, 40 hex characters.
"""

from datetime import date, datetime

import msgspec

type Moment = datetime
type Day = date
type Sha = str
type Slug = str
# A path inside the task's folder, as the record cites it: `reviews/review-2.json`.
type TaskPath = str


class Frozen(msgspec.Struct, frozen=True, kw_only=True, omit_defaults=True):
    """The base of every record: frozen, keyword fields, defaults left out of the JSON."""


class Tagged(Frozen, tag_field="kind", frozen=True, kw_only=True):
    """The base of each member of a union, told apart by its `kind`."""
