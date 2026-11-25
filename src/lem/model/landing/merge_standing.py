"""What a refusal of the merge keeps, and the owner's merge that a moved base refused
(`landing.md` D, "Standing merge"; E, "Owner merge refused for the base"; `main:land.cmd_merge`,
`kept_refusal`).

The merge agent's merge refused by Lem's rules is kept for its tip (`Refused`), so the server
tries that tip no more and the owner reads why. The owner's own word, for the tip he saw, refused
because the base moved, is kept with his merge standing: it stands while the proposal's tip and
the reasons it is not green, read again now, are the ones he saw, and the board's server carries
it out after a safe read. Only his word makes a standing merge: a refusal of the merge agent's,
of the server's or of his standing merge never does.
"""

from types import MappingProxyType
from typing import TYPE_CHECKING, Literal

import msgspec

from lem.kernel import files
from lem.model.landing import green, standing
from lem.records.landing.merge import Refused
from lem.records.landing.propose import Standing

if TYPE_CHECKING:
    from lem.kernel.errors import Refusal
    from lem.model.landing.merge_asked import Asked
    from lem.records.base import Moment
    from lem.records.record import Record

# The kind each refusal of Lem's rules is kept under (`main:land.REFUSALS`).
type Kind = Literal["base", "rule", "tip", "target"]
BASE: Kind = "base"
TIP: Kind = "tip"
KINDS: MappingProxyType[str, Kind] = MappingProxyType(
    {
        BASE: BASE,
        "merger-rule": "rule",
        TIP: TIP,
        "checks-changed": TIP,
        "target": "target",
    }
)


def digest_of(reasons: tuple[str, ...]) -> str:
    """One digest of the reasons a proposal is not green, which a standing merge keeps."""
    return files.digest(msgspec.json.encode(reasons))


def reasons_now(record: Record) -> tuple[str, ...]:
    """The reasons the proposal is not green, read again now (`green.reasons`). The careful
    lines of the fast track are the proposal's own: they follow from the tip and the shape,
    which a new proposal changes, and from a read of the settings' edit that only `propose`
    makes."""
    proposed = record.landing.proposed if record.landing else None
    seen = proposed.reasons if proposed else ()
    head = green.FAST.split("(", 1)[0]
    fast = tuple(reason for reason in seen if reason.startswith(head))
    return fast + green.reasons(record, ())


def standing_of(record: Record) -> Standing | None:
    """The owner's merge that stands for the proposed tip: his own word refused for the base,
    standing by `land-base`'s rule (`model/landing/standing.py`) with the reasons it is not
    green read again now; or the one `propose` found standing on a new tip."""
    landing = record.landing
    if landing is None or landing.standing is None or landing.proposed is None:
        return None
    judged = landing.proposed.owner_merge
    if landing.standing.tip != landing.proposed.tip:
        return landing.standing if judged and judged.state == "stands" else None
    now = digest_of(reasons_now(record))
    found = standing.standing(landing, now, carried=True)
    return landing.standing if found and found.state == "stands" else None


def word(asked: Asked) -> bool:
    """Whether `asked` is the owner's own word for the tip he saw: never the merge agent's,
    the server's, or his standing merge carried out."""
    return asked.by == "owner" and not asked.standing and asked.via != "server"


def refused_of(
    record: Record, refusal: Refusal, asked: Asked, now: Moment
) -> Refused | None:
    """The refusal kept for the proposed tip: the merge agent's by Lem's rules, or the
    owner's own word for the base; None for any other, which keeps nothing."""
    proposed = record.landing.proposed if record.landing else None
    kind = KINDS.get(refusal.code)
    keeps = asked.by == "merger" or (kind == BASE and word(asked))
    if proposed is None or kind is None or not keeps:
        return None
    line = f"{refusal.why}; {refusal.fix}"
    return Refused(
        tip=proposed.tip, source="lem", kind=kind, line=line, by=asked.by, at=now
    )


def kept(
    record: Record, refusal: Refusal, asked: Asked, now: Moment
) -> tuple[Refused, Standing | None] | None:
    """What a refusal keeps, to write together: its `Refused`, and for the owner's own word
    refused for the base his merge standing, with the reasons he saw."""
    refused = refused_of(record, refusal, asked, now)
    if refused is None:
        return None
    if refused.kind != BASE or not word(asked):
        return refused, None
    proposed = record.landing.proposed if record.landing else None
    seen = digest_of(proposed.reasons if proposed else ())
    return refused, Standing(
        tip=refused.tip, reasons_digest=seen, by_act=asked.via, at=now
    )
