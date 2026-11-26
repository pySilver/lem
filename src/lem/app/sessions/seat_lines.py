"""What `lem seat failed` decides and says: the seat that stands in, or the block, with the line
for the owner (`project.seat_call` and `call_head` on `main`)."""

from typing import TYPE_CHECKING

import msgspec

from lem.records.base import Frozen
from lem.records.holds import Blocked

if TYPE_CHECKING:
    from lem.records.work import StandIn

# Each error's words in the line of a stand-in or a block.
ERRORS = (
    ("missing", "its program is not on this Mac"),
    ("login", "it is not logged in"),
    ("tokens", "it has no tokens left"),
    ("usage-limit", "it reached its usage limit"),
    ("model", "it does not know the model"),
)
STAND_IN = "stand-in"


class Decision(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """The seat that stands in from now on (`blocked` false), or the block (`blocked` true),
    the seat that failed and its error, and the line the stage says to the owner."""

    task: str
    name: str
    blocked: bool
    seat: str | None
    source: str | None = msgspec.field(default=None, name="from")
    failed: str = msgspec.field(name="for")
    error: str
    say: str

    @classmethod
    def of(cls, slug: str, failure: StandIn) -> Decision:
        """The decision a failure on the task's record holds."""
        took = failure.took
        return cls(
            task=slug,
            name=failure.seat,
            blocked=took is None,
            seat=took,
            source=STAND_IN if took else None,
            failed=failure.failed,
            error=failure.error,
            say=said(failure),
        )


def said(failure: StandIn) -> str:
    """The line of a seat's error: the stand-in that took its place, or why none could."""
    why = dict(ERRORS)[failure.error]
    head = f"the {failure.seat}'s seat `{failure.failed}` gave an error: {why}"
    if failure.took is not None:
        return (
            f"{head}; `{failure.took}` stands in for it, and the pull request says so"
        )
    return f"{head}, and no fallback may stand in for it"


def blocked(slug: str, failure: StandIn) -> Blocked:
    """The block of a seat no fallback could take."""
    fix = f"lem seat again {slug} once the owner has fixed it"
    why = said(failure)
    return Blocked(why=why, fix=fix, seat=failure.seat, since=failure.at)
