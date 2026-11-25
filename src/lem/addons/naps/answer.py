"""What `lem nap may` gives."""

from lem.records.base import Frozen


class May(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """The answer: whether a nap may start, why, the naps' folder, the minute that names the
    new nap's folder, and the newest nap's folder."""

    may: bool
    why: str
    folder: str
    time: str | None = None
    newest: str | None = None
