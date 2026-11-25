"""The owner's presence, the machine's: `owner.json` in Lem's home folder.

It keeps each change he made, so that the spans a task ran without him can be read back
(`project.runs_without_owner` on `main`), and `seen` counts them, so that a watch that last saw
count N wakes on the next one (`project.cmd_owner_watch` on `main`). No file means he is there.
"""

from lem.records.base import Frozen, Moment


class Change(Frozen, frozen=True, kw_only=True):
    """One away or back he said: which, when, and his words."""

    away: bool
    at: Moment
    words: str | None = None


class Presence(Frozen, frozen=True, kw_only=True):
    """Whether the owner is away, since when, his words, how many changes there were, and each
    change."""

    away: bool = False
    since: Moment | None = None
    words: str | None = None
    seen: int = 0
    changes: tuple[Change, ...] = ()
