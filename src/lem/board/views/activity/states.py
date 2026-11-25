"""The look of a state as the charts and the feed draw it: a status, or the hold over it (the
owner's answer or a breaker, a block, his park), each with `rule.py`'s words, in the order of
the legend (`board_model.STATUS` on `main`)."""

from types import MappingProxyType

from lem.board.views import rule

HELD = "held"
BLOCKED = "blocked"
PARKED = "parked"
STATES = MappingProxyType(
    {
        **rule.STATUS,
        HELD: rule.HELD,
        BLOCKED: rule.BLOCKED,
        PARKED: rule.PARKED,
    }
)
# A state of a hold's kind is drawn as the hold, whatever its status.
HOLDS = MappingProxyType(
    {
        "owner": HELD,
        "breaker": HELD,
        BLOCKED: BLOCKED,
        "release": BLOCKED,
        PARKED: PARKED,
    }
)
UNKNOWN = rule.Said("bad", rule.NOBODY, "No status", "triangle-exclamation")
# The legend's order.
ORDER = (
    "queued",
    "shaping",
    "building",
    "planned",
    HELD,
    BLOCKED,
    "ready",
    "landing",
    "open",
    "landed",
    "dropped",
    "answered",
    PARKED,
)
# The states whose swatch has a look of its own beside the others of their color.
OWN_SWATCH = frozenset(("queued", "ready"))


def key_of(status: str, hold: str | None) -> str:
    """The state a status and the kind of the hold over it are drawn as."""
    return HOLDS.get(hold or "", status)


def said_of(key: str) -> rule.Said:
    """The words of a state; a status the board does not know says so."""
    return STATES.get(key, UNKNOWN)
