"""The owner's presence, the machine's: `owner.json` in Lem's home folder.

`seen` counts his changes, so that a watch that last saw count N wakes on the next one
(`project.cmd_owner_watch` on `main`). No file means he is there.
"""

from lem.records.base import Frozen, Moment


class Presence(Frozen, frozen=True, kw_only=True):
    """Whether the owner is away, since when, his words, and how many changes there were."""

    away: bool = False
    since: Moment | None = None
    words: str | None = None
    seen: int = 0
