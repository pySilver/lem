"""The owner's merge that a moved base refused, and what such a refusal keeps (`landing.md` D,
"Standing merge"; E, "Owner merge refused for the base"; `main:land.kept_refusal`).

A refusal of the merge for the base keeps Lem's refusal of the proposed tip, so the server tries
that tip no more; the owner's merge then stands, while the proposal's tip and the reasons it is
not green stay the same, and the board's server carries it out after a safe read.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.kernel import files
from lem.records.landing.merge import Refused
from lem.records.landing.propose import Standing

if TYPE_CHECKING:
    from lem.kernel.errors import Refusal
    from lem.model.landing.world import Merger
    from lem.records.base import Moment
    from lem.records.landing.record import Landing


def digest_of(reasons: tuple[str, ...]) -> str:
    """One digest of the reasons a proposal is not green, which a standing merge keeps."""
    return files.digest(msgspec.json.encode(reasons))


def standing_of(landing: Landing) -> Standing | None:
    """The owner's merge that stands for the proposed tip: refused for the base, with the
    reasons it is not green unchanged since (`landing.md` D, "Standing merge")."""
    proposed, standing = landing.proposed, landing.standing
    if proposed is None or standing is None or standing.tip != proposed.tip:
        return None
    return standing if standing.reasons_digest == digest_of(proposed.reasons) else None


def kept(
    landing: Landing, refusal: Refusal, asked: tuple[Merger, str], now: Moment
) -> tuple[Refused, Standing | None] | None:
    """What a refusal of the merge for the base keeps (`asked`: who asked, through what): its
    `Refused` of Lem for the proposed tip, so the server tries that tip no more, and, for the
    owner's merge, his merge standing until a safe read (`main:land.kept_refusal`). None for
    any other refusal, which keeps nothing."""
    proposed = landing.proposed
    if refusal.code != "base" or proposed is None:
        return None
    by, via = asked
    refused = Refused(
        tip=proposed.tip, source="lem", kind="base", line=refusal.why, by=by, at=now
    )
    if by != "owner":
        return refused, None
    standing = Standing(
        tip=proposed.tip,
        reasons_digest=digest_of(proposed.reasons),
        by_act=via,
        at=now,
    )
    return refused, standing
