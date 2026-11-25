"""What a refusal of the merge keeps, and the owner's merge that a moved base refused
(`landing.md` D, "Standing merge"; E, "Owner merge refused for the base"; `main:land.cmd_merge`,
`kept_refusal`).

The merge agent's merge refused by Lem's rules is kept for its tip (`Refused`), so the server
tries that tip no more and the owner reads why. The owner's own word, for the tip he saw, refused
because the base moved, is kept with his merge standing: it stands while the proposal's tip and
the reasons it is not green, read again now, are the ones he saw, and the board's server carries
it out after checks on the rebased change. Only his word makes a standing merge. The server
can record that the base moved again for an approval that already stands.
"""

from typing import TYPE_CHECKING, Literal

import msgspec

from lem.kernel import files
from lem.model.criteria import contract
from lem.model.landing import careful_words, green
from lem.records.landing.merge import Refused
from lem.records.landing.propose import Standing

if TYPE_CHECKING:
    from lem.kernel.errors import Refusal
    from lem.model.landing.merge_asked import Asked
    from lem.model.landing.world import World
    from lem.records.base import Moment
    from lem.records.record import Record

# The kind each refusal of Lem's rules is kept under (`main:land.REFUSALS`).
type Kind = Literal["base", "rule", "tip", "target"]
BASE: Kind = "base"
TIP: Kind = "tip"
KINDS: tuple[tuple[str, Kind], ...] = (
    (BASE, BASE),
    ("merger-rule", "rule"),
    (TIP, TIP),
    ("checks-changed", TIP),
    ("target", "target"),
)


def digest_of(reasons: tuple[str, ...], approved: str | None) -> str:
    """One digest of the reasons and criteria the owner saw."""
    return files.digest(msgspec.json.encode((reasons, approved)))


def reasons_now(record: Record, world: World | None = None) -> tuple[str, ...]:
    """The reasons the proposal is not green, read again now (`green.reasons`). The careful
    line of the fast track comes from the owner's word if he gave it, else from the proposal:
    only `propose` reads the settings the change edits."""
    proposed = record.landing.proposed if record.landing else None
    seen = proposed.reasons if proposed else ()
    head = green.FAST.split("(", 1)[0]
    fast = green.fast(record, careful_words.owner_says(record, owner=False))
    if not fast:
        fast = tuple(reason for reason in seen if reason.startswith(head))
    return fast + green.reasons(record, (), world)


def standing_of(record: Record, world: World | None = None) -> Standing | None:
    """The owner's merge that stands for the proposed tip: his own word refused for the base,
    standing by `land-base`'s rule (`model/landing/standing.py`) with the reasons it is not
    green read again now; or the one `propose` found standing on a new tip."""
    landing = record.landing
    if landing is None or landing.standing is None or landing.proposed is None:
        return None
    judged = landing.proposed.owner_merge
    if judged and judged.state == "ended":
        return None
    if landing.standing.tip != landing.proposed.tip and judged is None:
        return None
    running = landing.phase == "preparing" and landing.checked is None
    reasons = landing.proposed.reasons if running else reasons_now(record, world)
    now = digest_of(reasons, contract.mark(record.task))
    return landing.standing if now == landing.standing.reasons_digest else None


def word(asked: Asked) -> bool:
    """Whether `asked` is the owner's own word for the tip he saw: never the merge agent's,
    the server's, or his standing merge carried out."""
    return asked.by == "owner" and not asked.standing and asked.via != "server"


def kind_of(code: str) -> Kind | None:
    """The kind of a refusal the merge keeps."""
    return next((kind for name, kind in KINDS if name == code), None)


def refused_of(
    record: Record, refusal: Refusal, asked: Asked, now: Moment
) -> Refused | None:
    """The refusal kept for the proposed tip: the merge agent's by Lem's rules, or the
    owner's own word for the base; None for any other, which keeps nothing."""
    proposed = record.landing.proposed if record.landing else None
    kind = kind_of(refusal.code)
    approved = word(asked) or asked.standing
    keeps = asked.by == "merger" or (kind == BASE and approved)
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
    refused for the base his merge standing, with the reasons and criteria he saw."""
    refused = refused_of(record, refusal, asked, now)
    if refused is None:
        return None
    if refused.kind != BASE or not word(asked):
        return refused, None
    proposed = record.landing.proposed if record.landing else None
    if proposed is None:
        return refused, None
    seen = digest_of(proposed.reasons, proposed.contract)
    return refused, Standing(
        tip=refused.tip, reasons_digest=seen, by_act=asked.via, at=now
    )
